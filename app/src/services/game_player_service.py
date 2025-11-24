from typing import Optional

from src.repositories import GamePlayerRepository
from src.schemas import GamePlayerTeamResponse


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
