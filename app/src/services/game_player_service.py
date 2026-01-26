from typing import Optional

from src.repositories import GamePlayerRepository
from src.schemas import GamePlayerRequest, GamePlayerTeamResponse
from src.services.game_service import ExceptionGameNotFound, GameService
from src.services.player_service import PlayerService


class GamePlayerService:
    def __init__(self):
        self.repository = GamePlayerRepository()

    def upsert_game_player(
        self,
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

        resp = self.repository.upsert(data)

        return resp

    def delete_player_in_game(self, game_id, player_id):
        return self.repository.delete(game_id, player_id)

    def get_player_by_id_in_game(self, game_id, player_id):
        return self.repository.get_by_player_id(game_id, player_id)

    def update_game_player(self, game_id, player_id, payload):
        player_service = PlayerService()
        invited_by = payload.get("invited_by")
        if invited_by:
            payload["invited_by"] = player_service.resolve_or_create_player(invited_by)

        return self.repository.update(game_id, player_id, payload)

    def add_player_in_game(self, game_id: str, data: GamePlayerRequest):
        # Validar se o game_id existe
        game_service = GameService()
        if not game_service.get_game_by_id(game_id):
            raise ExceptionGameNotFound

        # Resolver ou criar o jogador
        player_service = PlayerService()
        player_id = player_service.resolve_or_create_player(data.name).id

        # Resolver ou criar o jogador que convidou, se aplicável
        invited_by_id = None
        if data.is_visitor is True:
            if data.invited_by:
                invited_by_id = player_service.resolve_or_create_player(
                    data.invited_by
                ).id
            else:
                raise Exception("O jogador visitante deve ter um convidador.")

        # Inserir ou atualizar o jogador no jogo
        data = {
            "game_id": game_id,
            "player_id": player_id,
            "is_goalkeeper": data.is_goalkeeper,
            "is_visitor": data.is_visitor,
            "invited_by": invited_by_id,
            "paid": data.paid,
            "team": data.team,
        }

        self.repository.upsert(data)
