from dotenv import load_dotenv

load_dotenv()

import os
from datetime import date
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import (
    GamePlayerRequest,
    GamePlayerTeamResponse,
    GamePlayerUpdate,
    GameRequest,
    GameResponse,
    GenerateTeamsRequest,
    GenerateTeamsResponse,
    PlayerResponse,
)
from src.services import GamePlayerService, GameTeamService, PlayerService
from supabase import Client, create_client

game_team_service = GameTeamService()
player_service = PlayerService()
game_player_service = GamePlayerService()


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


# 1) Rota para criar (ou garantir) um game
@app.post("/games", response_model=GameResponse, tags=["games"])
def create_game(payload: GameRequest):
    game = ensure_game(payload.game_date)
    return game


# -------------------------------------------------------------------
# GET /games - lista jogos (opcionalmente por período)
# -------------------------------------------------------------------
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


# -------------------------------------------------------------------
# GET /games/{game_id} - detalhe do jogo
# -------------------------------------------------------------------
@app.get("/games/{game_id}", response_model=GameResponse, tags=["games"])
def get_game(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
):
    resp = supabase.table("games").select("*").eq("id", game_id).limit(1).execute()

    if not resp.data:
        raise HTTPException(status_code=404, detail="Game não encontrado")

    return resp.data[0]


# -------------------------------------------------------------------
# DELETE /games/{game_id} - remove um jogo (e seus vínculos)
# -------------------------------------------------------------------
@app.delete("/games/{game_id}", status_code=204, tags=["games"])
def delete_game(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
):
    resp = supabase.table("games").delete().eq("id", game_id).execute()

    # Se nenhum registro foi removido, retorna 404
    if not resp.data:
        raise HTTPException(status_code=404, detail="Game não encontrado")

    # 204 No Content
    return


# -------------------------------------------------------------------
# GET /games/{game_id}/players - lista jogadores do jogo
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


# -------------------------------------------------------------------
# POST /games/{game_id}/players - adiciona um jogador ao jogo
# -------------------------------------------------------------------
@app.post(
    "/games/{game_id}/players",
    response_model=GamePlayerTeamResponse,
    tags=["games/players"],
)
def add_player_to_game(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
    body: GamePlayerRequest = ...,
):
    # garante que o jogo existe
    game_resp = (
        supabase.table("games").select("id").eq("id", game_id).limit(1).execute()
    )
    if not game_resp.data:
        raise HTTPException(status_code=404, detail="Game não encontrado")

    # resolve/cria jogador principal
    player_id = resolve_or_create_player(body.name)
    if not player_id:
        raise HTTPException(status_code=500, detail="Falha ao resolver jogador")

    # resolve/cria convidador (se enviado)
    invited_by_id = None
    if body.invited_by:
        invited_by_id = resolve_or_create_player(body.invited_by)

    upsert_game_player(
        game_id=game_id,
        player_id=player_id,
        is_goalkeeper=body.is_goalkeeper,
        is_visitor=body.is_visitor,
        invited_by_id=invited_by_id,
        team=body.team,
    )

    return GamePlayerTeamResponse(
        name=body.name,
        is_goalkeeper=body.is_goalkeeper,
        is_visitor=body.is_visitor,
        team=body.team,
    )


# -------------------------------------------------------------------
# PATCH /games/{game_id}/players/{game_player_id} - atualiza flags/time
# -------------------------------------------------------------------
@app.patch(
    "/games/{game_id}/players/{player_id}",
    response_model=GamePlayerTeamResponse,
    tags=["games/players"],
)
def update_game_player(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
    player_id: str = Path(
        ...,
        description="ID do registro em players",
        example="5bb2b67d-5f9e-4a37-b32e-0a2f2b8cb6fc",
    ),
    body: GamePlayerUpdate = ...,
):
    # monta dict de update
    update_data: Dict[str, object] = {}
    if body.is_goalkeeper is not None:
        update_data["is_goalkeeper"] = body.is_goalkeeper
    if body.is_visitor is not None:
        update_data["is_visitor"] = body.is_visitor
    if body.paid is not None:
        update_data["paid"] = body.paid
    if body.team is not None:
        update_data["team"] = body.team

    invited_by_id = None
    if body.invited_by is not None:
        # se vier string vazia, zera; se vier nome, resolve/cria
        if body.invited_by.strip() == "":
            invited_by_id = None
        else:
            invited_by_id = resolve_or_create_player(body.invited_by)
        update_data["invited_by"] = invited_by_id

    if not update_data:
        raise HTTPException(status_code=400, detail="Nada para atualizar")

    resp = (
        supabase.table("game_players")
        .update(update_data)
        .eq("game_id", game_id)
        .eq("player_id", player_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(
            status_code=404, detail="Registro de game_player não encontrado"
        )

    row = resp.data[0]

    # busca nome do jogador
    player_name = "Desconhecido"
    if row.get("player_id"):
        pl_resp = (
            supabase.table("players")
            .select("name")
            .eq("id", row["player_id"])
            .limit(1)
            .execute()
        )
        if pl_resp.data:
            player_name = pl_resp.data[0]["name"]

    return GamePlayerTeamResponse(
        id=row["id"],
        name=player_name,
        is_goalkeeper=row.get("is_goalkeeper", False),
        is_visitor=row.get("is_visitor", False),
        paid=row.get("paid", False),
        team=row.get("team"),
    )


# -------------------------------------------------------------------
# DELETE /games/{game_id}/players/{game_player_id} - remove jogador do jogo
# -------------------------------------------------------------------
@app.delete(
    "/games/{game_id}/players/{game_player_id}", status_code=204, tags=["games/players"]
)
def delete_game_player(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
    game_player_id: str = Path(
        ...,
        description="ID do registro em game_players",
        example="5bb2b67d-5f9e-4a37-b32e-0a2f2b8cb6fc",
    ),
):
    resp = (
        supabase.table("game_players")
        .delete()
        .eq("id", game_player_id)
        .eq("game_id", game_id)
        .execute()
    )

    # se quiser, pode checar resp.data pra ver se algo foi deletado:
    # if not resp.data: raise HTTPException(404, "Registro não encontrado")

    return


# 2) Rota para gerar times para um game existente
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
    teams = game_team_service.generate_teams(
        parsed_players, body.zagueiros_fixos, body.habilidosos, body.players_per_team
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

    return teams
