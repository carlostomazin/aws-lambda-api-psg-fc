from dotenv import load_dotenv

load_dotenv()


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import GenerateTeamsRequest
from src.services import (
    GameAddSchema,
    GamePlayerAddSchema,
    GamePlayerService,
    GamePlayerUpdateSchema,
    GameService,
    GameTeamService,
    GameUpdateSchema,
    PlayerService,
)

# Inicializa serviços
game_team_service = GameTeamService()
player_service = PlayerService()
game_player_service = GamePlayerService()
game_service = GameService()

# Inicializa FastAPI
app = FastAPI(title="Football Games API")

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
#  Raiz
# -------------------------------------------------------------------
@app.get("/")
def health():
    return {"message": "ok"}


# -------------------------------------------------------------------
#  /players
# -------------------------------------------------------------------
@app.get("/players/{player_id}", tags=["players"])
def get_player_by_id(player_id: str):
    return player_service.get_player_by_id(player_id)


@app.get("/players/{player_id}/games", tags=["players"])
def get_games_by_player_id(player_id: str):
    return player_service.get_games_by_player_id(player_id)


@app.get("/players", tags=["players"])
def get_players():
    return player_service.get_players()


@app.delete("/players/{player_id}", status_code=204, tags=["players"])
def delete_player(player_id: str):
    return player_service.delete_player(player_id)


# -------------------------------------------------------------------
#  /games
# -------------------------------------------------------------------
@app.post("/games", tags=["games"])
def create_game(body: GameAddSchema):
    return game_service.get_or_create_game(body)


@app.patch("/games/{game_id}", tags=["games"])
def update_game(game_id: str, body: GameUpdateSchema):
    return game_service.update_game(game_id, body)


@app.get("/games", tags=["games"])
def get_games():
    return game_service.get_games()


@app.get("/games/{game_id}", tags=["games"])
def get_game(game_id: str):
    return game_service.get_game(game_id)


@app.delete("/games/{game_id}", tags=["games"])
def delete_game(game_id: str):
    return game_service.delete_game(game_id)


# -------------------------------------------------------------------
#  /games/players
# -------------------------------------------------------------------
@app.post("/games/{game_id}/players", tags=["games/players"])
def add_player_in_game(game_id: str, body: GamePlayerAddSchema):
    return game_player_service.add_player_in_game(game_id, body)


@app.patch("/games/{game_id}/players/{player_id}", tags=["games/players"])
def update_player_in_game(game_id: str, player_id: str, body: GamePlayerUpdateSchema):
    player = game_player_service.get_player_in_game(game_id, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found in game")
    return game_player_service.update_player_in_game(game_id, player_id, body)


@app.get("/games/{game_id}/players", tags=["games/players"])
def get_players_in_game(game_id: str):
    return game_player_service.get_players_in_game(game_id)


@app.delete("/games/{game_id}/players/{player_id}", tags=["games/players"])
def delete_player_in_game(game_id: str, player_id: str):
    return game_player_service.delete_player_in_game(game_id, player_id)


# -------------------------------------------------------------------
#  /games/teams
# -------------------------------------------------------------------
@app.post("/games/{game_id}/teams/generate", tags=["games/teams"])
def generate_teams_for_game(game_id: str, body: GenerateTeamsRequest):
    # 1) parse do texto
    parsed_players = game_team_service.parse_jogadores_raw(body.jogadores_raw)

    for player in parsed_players:
        if player["invited_by_name"]:
            player["invited_by_id"] = player_service.get_or_create_player(player["invited_by_name"])["id"]
        else:
            player["invited_by_id"] = None

        player["player_id"] = player_service.get_or_create_player(player["name"])["id"]

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
