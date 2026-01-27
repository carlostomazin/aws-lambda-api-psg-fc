from dotenv import load_dotenv

load_dotenv()

import os
from datetime import date
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import (
    GamePlayerTeamResponse,
    GameRequest,
    GameResponse,
    GameUpdate,
    GenerateTeamsRequest,
    PlayerResponse,
)
from src.services import (
    GamePlayerAddSchema,
    GamePlayerService,
    GamePlayerUpdateSchema,
    GameService,
    GameTeamService,
    PlayerService,
)
from supabase import Client, create_client

game_team_service = GameTeamService()
player_service = PlayerService()
game_player_service = GamePlayerService()
game_service = GameService()


# -------------------------------------------------------------------
# Supabase client
# -------------------------------------------------------------------
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -------------------------------------------------------------------
# Helpers de banco (Supabase)
# -------------------------------------------------------------------
def ensure_game(game_date: date) -> dict:
    """Retorna o jogo da data, criando se não existir."""
    resp = (
        supabase.table("games")
        .select("*")
        .eq("game_date", game_date.isoformat())
        .limit(1)
        .execute()
    )

    if resp.data:
        return resp.data[0]

    insert_resp = (
        supabase.table("games").insert({"game_date": game_date.isoformat()}).execute()
    )

    if not insert_resp.data:
        raise HTTPException(status_code=500, detail="Erro ao criar jogo")

    return insert_resp.data[0]


def resolve_or_create_player(name_raw: str) -> str | None:
    if not name_raw:
        return None

    name_clean = name_raw.strip()

    resp = (
        supabase.table("players")
        .select("id, name")
        .ilike("name", name_clean)
        .limit(1)
        .execute()
    )

    if resp.data:
        return resp.data[0]["id"]

    insert_resp = supabase.table("players").insert({"name": name_clean}).execute()

    if not insert_resp.data:
        raise HTTPException(status_code=500, detail="Erro ao criar jogador")

    return insert_resp.data[0]["id"]


def upsert_game_player(
    game_id: str,
    player_id: str,
    is_goalkeeper: bool,
    is_visitor: bool,
    invited_by_id: Optional[str],
    team: Optional[str],
) -> GamePlayerTeamResponse:
    data = {
        "game_id": game_id,
        "player_id": player_id,
        "is_goalkeeper": is_goalkeeper,
        "is_visitor": is_visitor,
        "invited_by": invited_by_id,
        "team": team,
    }

    try:
        resp = (
            supabase.table("game_players")
            .upsert(data, on_conflict="game_id,player_id")
            .execute()
        )
    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar game_player: {err}"
        )

    if not resp.data:
        raise HTTPException(status_code=500, detail="Erro ao salvar game_player")

    return GamePlayerTeamResponse.model_validate(resp.data[0])


# -------------------------------------------------------------------
# Helpers de texto / parsing
# -------------------------------------------------------------------
def generate_teams(parsed_players, zagueiros_fixos, habilidosos, teams_count=2):
    defenders = []
    skilled = []
    others = []

    for p in parsed_players:
        n = p["name_norm"]
        if n in zagueiros_fixos:
            defenders.append(p)
        elif n in habilidosos:
            skilled.append(p)
        else:
            others.append(p)

    teams = {chr(ord("A") + i): [] for i in range(teams_count)}

    def distribute(lst):
        i = 0
        keys = list(teams.keys())
        for item in lst:
            teams[keys[i]].append(item)
            i = (i + 1) % len(keys)

    distribute(defenders)
    distribute(skilled)
    distribute(others)

    for key, players in teams.items():
        for p in players:
            p["team"] = key

    return teams


app = FastAPI(title="Football Games API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"message": "ok"}


# -------------------------------------------------------------------
#  /players
# -------------------------------------------------------------------
@app.get("/players/{player_id}", tags=["players"])
def get_player_by_id(player_id: str):
    resp = player_service.get_player_by_id(player_id)
    return resp


@app.get("/players/{player_id}/games", tags=["players"])
def get_games_by_player_id(player_id: str):
    resp = player_service.get_games_by_player_id(player_id)
    return resp


@app.get("/players", response_model=List[PlayerResponse], tags=["players"])
def list_players():
    resp = player_service.list_all_players()
    return resp


@app.delete("/players/{player_id}", status_code=204, tags=["players"])
def delete_player(player_id: str):
    resp = player_service.delete_player(player_id)
    return resp


# -------------------------------------------------------------------
#  /games
# -------------------------------------------------------------------
@app.post("/games", response_model=GameResponse, tags=["games"])
def create_game(payload: GameRequest):
    return ensure_game(payload.game_date)


@app.patch("/games/{game_id}", tags=["games"])
def update_game(game_id: str, body: GameUpdate):
    update_data: Dict[str, object] = {}
    if body.game_date is not None:
        update_data["game_date"] = str(body.game_date)
    if body.game_price is not None:
        update_data["game_price"] = body.game_price
    if body.price_per_player is not None:
        update_data["price_per_player"] = body.price_per_player
    if body.goalkeepers_pay is not None:
        update_data["goalkeepers_pay"] = body.goalkeepers_pay

    return game_service.update_game(game_id, update_data)


@app.get("/games", response_model=List[GameResponse], tags=["games"])
def list_games(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    query = supabase.table("games").select("*")

    if from_date:
        query = query.gte("game_date", from_date.isoformat())
    if to_date:
        query = query.lte("game_date", to_date.isoformat())

    resp = query.order("game_date", desc=True).execute()

    return resp.data or []


@app.get("/games/{game_id}", response_model=GameResponse, tags=["games"])
def get_game(game_id: str):
    resp = supabase.table("games").select("*").eq("id", game_id).limit(1).execute()

    if not resp.data:
        raise HTTPException(status_code=404, detail="Game não encontrado")

    return resp.data[0]


@app.delete("/games/{game_id}", status_code=204, tags=["games"])
def delete_game(game_id: str):
    resp = supabase.table("games").delete().eq("id", game_id).execute()

    if not resp.data:
        raise HTTPException(status_code=404, detail="Game não encontrado")

    return


# -------------------------------------------------------------------
#  /games/players
# -------------------------------------------------------------------
@app.get(
    "/games/{game_id}/players",
    response_model=List[GamePlayerTeamResponse],
    tags=["games/players"],
)
def list_game_players(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="878973b4-f837-4647-be14-eb3e54895c1e",
    ),
):
    # pega game_players do jogo
    gp_resp = (
        supabase.table("game_players")
        .select(
            "id, created_at, updated_at, is_goalkeeper, is_visitor, paid, team, player:player_id (*), player_invited:invited_by (*)"
        )
        .eq("game_id", game_id)
        .execute()
    )

    game_players = gp_resp.data or []
    if not game_players:
        return []

    return game_players


@app.post("/games/{game_id}/players", tags=["games/players"])
def add_player_in_game(game_id: str, body: GamePlayerAddSchema):
    return game_player_service.add_player_in_game(game_id, body)


@app.patch("/games/{game_id}/players/{player_id}", tags=["games/players"])
def update_player_in_game(game_id: str, player_id: str, body: GamePlayerUpdateSchema):
    return game_player_service.update_player_in_game(game_id, player_id, body)


@app.delete(
    "/games/{game_id}/players/{player_id}", status_code=204, tags=["games/players"]
)
def delete_player_in_game(game_id: str, player_id: str):
    game_player_service.delete_player_in_game(game_id, player_id)


# -------------------------------------------------------------------
#  /games/teams
# -------------------------------------------------------------------
@app.post(
    "/games/{game_id}/teams/generate",
    # response_model=GenerateTeamsResponse,
    tags=["games/teams"],
)
def generate_teams_for_game(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
    body: GenerateTeamsRequest = ...,
):
    # 1) parse do texto
    parsed_players = game_team_service.parse_jogadores_raw(body.jogadores_raw)

    for player in parsed_players:
        if player["invited_by_name"]:
            player["invited_by_id"] = player_service.resolve_or_create_player(
                player["invited_by_name"]
            ).id
        else:
            player["invited_by_id"] = None

        player["player_id"] = player_service.resolve_or_create_player(player["name"]).id

    # 2) gera times (apenas em memória)
    goalkeepers = [dict(p) for p in parsed_players if p["is_goalkeeper"] is True]
    players = [dict(j) for j in parsed_players if j["is_goalkeeper"] is False]

    teams = game_team_service.generate_teams(
        players,
        body.zagueiros_fixos,
        body.habilidosos,
        body.players_per_team,
    )

    for team_name, players in teams.items():
        for p in players:
            game_player_service.upsert_game_player(
                game_id,
                p["player_id"],
                p["is_goalkeeper"],
                p["is_visitor"],
                p["invited_by_id"],
                p["team"],
            )

    for g in goalkeepers:
        game_player_service.upsert_game_player(
            game_id,
            g["player_id"],
            g["is_goalkeeper"],
            g["is_visitor"],
            g["invited_by_id"],
            None,
        )

    return teams
