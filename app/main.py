import os
import re
import unicodedata
from datetime import date
from typing import Dict, List, Optional

from dotenv import load_dotenv
from emoji import replace_emoji
from fastapi import FastAPI, HTTPException, Path
from schemas import (
    GameCreate,
    GameOut,
    GamePlayerCreate,
    GamePlayerUpdate,
    GenerateTeamsRequest,
    GenerateTeamsResponse,
    PlayerTeamOut,
)
from supabase import Client, create_client

load_dotenv()


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
    *,
    is_goalkeeper: bool,
    is_visitor: bool,
    invited_by_id: Optional[str],
    team: Optional[str],
):
    data = {
        "game_id": game_id,
        "player_id": player_id,
        "is_goalkeeper": is_goalkeeper,
        "is_visitor": is_visitor,
        "invited_by": invited_by_id,
        # ATENÇÃO: aqui você está usando coluna "team".
        # Se no banco for "teams", troca a chave abaixo pra "teams".
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

    return resp.data[0]


# -------------------------------------------------------------------
# Helpers de texto / parsing
# -------------------------------------------------------------------
def normalize_name(name: str) -> str:
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    only_ascii = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", only_ascii).strip().lower()


def parse_jogadores_raw(jogadores_raw: str):
    jogadores_raw = replace_emoji(jogadores_raw, replace="")

    lines = jogadores_raw.splitlines()
    section = None
    players = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "GOLEIROS" in line.upper():
            section = "goleiros"
            continue
        if "DA CASA" in line.upper():
            section = "casa"
            continue
        if "VISITANTES" in line.upper():
            section = "visitantes"
            continue
        if "NÃO VÃO" in line.upper() or "NAO VAO" in line.upper():
            section = "nao_vao"
            continue

        m = re.match(r"^\d+\.\s*(.+)$", line)
        if not m or section is None:
            continue

        raw = m.group(1).strip()
        if not raw or raw == ".":
            continue

        paren = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", raw)
        invited_by_name = None
        name_part = raw
        if paren:
            name_part = paren.group(1).strip()
            invited_by_name = paren.group(2).strip()

        if section == "nao_vao":
            continue

        players.append(
            {
                "name_raw": name_part,
                "name_norm": normalize_name(name_part),
                "invited_by_name_raw": invited_by_name,
                "invited_by_name_norm": (
                    normalize_name(invited_by_name) if invited_by_name else None
                ),
                "is_goalkeeper": section == "goleiros",
                "is_visitor": section == "visitantes",
            }
        )

    return players


def generate_teams(parsed_players, zagueiros_fixos, habilidosos, teams_count=2):
    zagueiros_fixos_norm = {normalize_name(n) for n in zagueiros_fixos}
    habilidosos_norm = {normalize_name(n) for n in habilidosos}

    defenders = []
    skilled = []
    others = []

    for p in parsed_players:
        n = p["name_norm"]
        if n in zagueiros_fixos_norm:
            defenders.append(p)
        elif n in habilidosos_norm:
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


@app.get("/")
def health():
    return {"message": "ok"}


# 1) Rota para criar (ou garantir) um game
@app.post("/games", response_model=GameOut, tags=["games"])
def create_game(payload: GameCreate):
    game = ensure_game(payload.game_date)
    return game


# -------------------------------------------------------------------
# GET /games - lista jogos (opcionalmente por período)
# -------------------------------------------------------------------
@app.get("/games", response_model=List[GameOut], tags=["games"])
def list_games(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    query = supabase.table("games").select("*")

    if from_date:
        query = query.gte("game_date", from_date.isoformat())
    if to_date:
        query = query.lte("game_date", to_date.isoformat())

    resp = query.order("game_date").execute()

    return resp.data or []


# -------------------------------------------------------------------
# GET /games/{game_id} - detalhe do jogo
# -------------------------------------------------------------------
@app.get("/games/{game_id}", response_model=GameOut, tags=["games"])
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
# GET /games/{game_id}/players - lista jogadores do jogo
# -------------------------------------------------------------------
@app.get(
    "/games/{game_id}/players",
    response_model=List[PlayerTeamOut],
    tags=["games/players"],
)
def list_game_players(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
):
    # pega game_players do jogo
    gp_resp = (
        supabase.table("game_players")
        .select("id, player_id, is_goalkeeper, is_visitor, team")
        .eq("game_id", game_id)
        .execute()
    )

    game_players = gp_resp.data or []
    if not game_players:
        return []

    # busca nomes dos jogadores na tabela players
    player_ids = list({gp["player_id"] for gp in game_players if gp.get("player_id")})

    players_map: Dict[str, str] = {}
    if player_ids:
        pl_resp = (
            supabase.table("players").select("id, name").in_("id", player_ids).execute()
        )
        for row in pl_resp.data or []:
            players_map[row["id"]] = row["name"]

    result: List[PlayerTeamOut] = []
    for gp in game_players:
        name = players_map.get(gp["player_id"], "Desconhecido")
        result.append(
            PlayerTeamOut(
                id=gp["player_id"],
                name=name,
                is_goalkeeper=gp.get("is_goalkeeper", False),
                is_visitor=gp.get("is_visitor", False),
                team=gp.get("team"),
            )
        )

    return result


# -------------------------------------------------------------------
# POST /games/{game_id}/players - adiciona um jogador ao jogo
# -------------------------------------------------------------------
@app.post(
    "/games/{game_id}/players", response_model=PlayerTeamOut, tags=["games/players"]
)
def add_player_to_game(
    game_id: str = Path(
        ...,
        description="ID do jogo (UUID)",
        example="0ff24608-a1c8-43d4-a6a4-074a769d1bd7",
    ),
    body: GamePlayerCreate = ...,
):
    # garante que o jogo existe
    game_resp = (
        supabase.table("games").select("id").eq("id", game_id).limit(1).execute()
    )
    if not game_resp.data:
        raise HTTPException(status_code=404, detail="Game não encontrado")

    # resolve/ cria jogador principal
    player_id = resolve_or_create_player(body.name)
    if not player_id:
        raise HTTPException(status_code=500, detail="Falha ao resolver jogador")

    # resolve convidador (se enviado)
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

    return PlayerTeamOut(
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
    response_model=PlayerTeamOut,
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

    return PlayerTeamOut(
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
    response_model=GenerateTeamsResponse,
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
    # garante que o jogo existe
    game_resp = (
        supabase.table("games")
        .select("id, game_date")
        .eq("id", game_id)
        .limit(1)
        .execute()
    )

    if not game_resp.data:
        raise HTTPException(status_code=404, detail="Game não encontrado")

    # 1) parse do texto
    parsed_players = parse_jogadores_raw(body.jogadores_raw)

    # 2) gera times (apenas em memória)
    teams = generate_teams(
        parsed_players,
        body.zagueiros_fixos,
        body.habilidosos,
    )

    # 3) reflete no banco (players + game_players)
    for team_name, players in teams.items():
        for p in players:
            # aqui você estava usando name_norm no resolve_or_create_player,
            # mas sua função procura por name "bonitinho" (com maiúscula etc).
            # Se quiser, pode trocar pra p["name_raw"].
            player_id = resolve_or_create_player(p["name_raw"])
            invited_by_id = resolve_or_create_player(p["invited_by_name_raw"])
            upsert_game_player(
                game_id=game_id,
                player_id=player_id,
                is_goalkeeper=p["is_goalkeeper"],
                is_visitor=p["is_visitor"],
                invited_by_id=invited_by_id,
                team=team_name,
            )

    # 4) monta resposta bonita
    response_teams: Dict[str, List[PlayerTeamOut]] = {}
    for team_name, players in teams.items():
        response_teams[team_name] = [
            PlayerTeamOut(
                name=p["name_raw"],
                is_goalkeeper=p["is_goalkeeper"],
                is_visitor=p["is_visitor"],
                team=p.get("team"),
            )
            for p in players
        ]

    return GenerateTeamsResponse(
        game_id=game_id,
        teams=response_teams,
    )
