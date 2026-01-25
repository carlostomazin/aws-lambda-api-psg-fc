from typing import Dict, Optional

from src.repositories import GamePlayerRepository
from src.schemas import GamePlayerRequest, GamePlayerTeamResponse
from src.services.player_service import PlayerService
from src.services.game_service import GameService, ExceptionGameNotFound


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

    def delete_game_player(self, player_id, game_id):
        return self.repository.delete(player_id, game_id)

    def update_game_player(self, game_id, player_id, payload):
        player_service = PlayerService()
        invited_by = payload.get("invited_by")
        if invited_by:
            payload["invited_by"] = player_service.resolve_or_create_player(invited_by)

        return self.repository.update(game_id, player_id, payload)
    
    def add_player_to_game(
        self,
        game_id: str,
        data: GamePlayerRequest
    ):
        # Validar se o game_id existe
        game_service = GameService()
        if not game_service.get_game_by_id(game_id):
            raise ExceptionGameNotFound

        # Resolver ou criar o jogador
        player_service = PlayerService()
        player_id = player_service.resolve_or_create_player(data.name).id

        # Resolver ou criar o jogador que convidou, se aplicável
        invited_by_id = None
        if data.invited_by:
            invited_by_id = player_service.resolve_or_create_player(data.invited_by).id
        
        # Inserir ou atualizar o jogador no jogo
        self.upsert_game_player(
            game_id=game_id,
            player_id=player_id,
            is_goalkeeper=data.is_goalkeeper,
            is_visitor=data.is_visitor,
            invited_by_id=invited_by_id,
            team=data.team
        )
