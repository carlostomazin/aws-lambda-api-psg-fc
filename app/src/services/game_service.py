from datetime import date
from typing import Dict, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from src.repositories import GameRepository


class GameAddSchema(BaseModel):
    game_date: date
    game_price: Optional[float] = 0.00
    price_per_player: Optional[float] = 0.00
    goalkeepers_pay: Optional[bool] = False


class GameService:
    def __init__(self):
        self.repository = GameRepository()

    def get_game_by_id(self, game_id: str) -> dict | None:
        return self.repository.get_by_id(game_id)

    def get_game_by_date(self, game_date: date) -> dict | None:
        game_date = game_date.isoformat()
        return self.repository.get_by_date(game_date)

    def get_or_create_game(self, payload: GameAddSchema) -> dict | None:
        game = self.get_game_by_date(payload.game_date)
        if game:
            return game
        return self.repository.create(payload)

    def update_game(self, game_id: str, payload: Dict[str, object]) -> dict | None:
        return self.repository.update(game_id, payload)
