from fastapi import HTTPException
from src.repositories import GamePlayerRepository, PlayerRepository
from src.schemas import PlayerResponse


class PlayerService:
    def __init__(self):
        self.repository = PlayerRepository()
        self.game_player_repository = GamePlayerRepository()

    def get_player_by_id(self, player_id: str) -> dict | None:
        return self.repository.get_by_id(player_id)

    def get_games_by_player_id(self, player_id: str) -> list[dict] | None:
        return self.game_player_repository.get_by_player_id(player_id)

    def resolve_or_create_player(self, name: str) -> PlayerResponse:
        name_clean = name.strip()

        resp = self.repository.get_by_name(name_clean)

        if resp:
            return PlayerResponse.model_validate(resp)

        insert_resp = self.repository.create(name_clean)

        if not insert_resp:
            raise HTTPException(status_code=500, detail="Erro ao criar jogador")

        return PlayerResponse.model_validate(insert_resp)

    def list_all_players(self) -> list[PlayerResponse]:
        resp = self.repository.get_all()

        if resp:
            return [PlayerResponse.model_validate(i) for i in resp]

        return []

    def delete_player(self, player_id) -> None:
        resp = self.repository.delete(player_id)

        if resp:
            return resp
        return None
