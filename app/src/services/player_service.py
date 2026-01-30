from pydantic import BaseModel
from src.repositories import GamePlayerRepository, PlayerRepository


class PlayerAddSchema(BaseModel):
    name: str


class PlayerService:
    def __init__(self):
        self.repository = PlayerRepository()
        self.game_player_repository = GamePlayerRepository()

    def get_or_create_player(self, body: PlayerAddSchema) -> dict:
        body.name = body.name.strip()
        player = self.get_player_by_name(body.name)
        if player:
            return player
        return self.repository.create(body.model_dump())

    def get_player_by_id(self, player_id: str) -> dict | None:
        return self.repository.get({"id": player_id})[0]

    def get_games_by_player_id(self, player_id: str) -> list[dict] | None:
        return self.game_player_repository.get_games(player_id)

    def get_player_by_name(self, name: str) -> dict | None:
        name = name.strip()
        return self.repository.get({"name": name})[0]

    def get_players(self) -> list[dict]:
        return self.repository.get()

    def delete_player(self, player_id) -> None:
        return self.repository.delete(player_id)
