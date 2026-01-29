from datetime import date
from typing import Optional

from pydantic import BaseModel
from src.repositories import GameRepository


class GameAddSchema(BaseModel):
    game_date: date
    game_price: Optional[float] = 0.00
    price_per_player: Optional[float] = 0.00
    goalkeepers_pay: Optional[bool] = False


class GameUpdateSchema(BaseModel):
    game_date: date = None
    game_price: float = None
    price_per_player: float = None
    goalkeepers_pay: bool = None


class GameService:
    def __init__(self):
        self.repository = GameRepository()

    def get_game(self, game_id: str) -> dict | None:
        return self.repository.get_by_id(game_id)

    def get_game_by_date(self, game_date: date) -> dict | None:
        game_date = game_date.isoformat()
        return self.repository.get_by_date(game_date)

    def get_games(self) -> list[dict]:
        return self.repository.get_all()

    def get_or_create_game(self, body: GameAddSchema) -> dict | None:
        game = self.get_game_by_date(body.game_date)
        if game:
            return game
        body = body.model_dump()
        body["game_date"] = body["game_date"].isoformat()
        return self.repository.create(body)

    def update_game(self, game_id: str, body: GameUpdateSchema) -> dict | None:
        # Prepara os dados para atualização
        update_data = {}
        if body.game_date:
            update_data["game_date"] = str(body.game_date)
        if body.game_price:
            update_data["game_price"] = body.game_price
        if body.price_per_player:
            update_data["price_per_player"] = body.price_per_player
        if body.goalkeepers_pay:
            update_data["goalkeepers_pay"] = body.goalkeepers_pay

        return self.repository.update(game_id, update_data)

    def delete_game(self, game_id: str) -> None:
        return self.repository.delete(game_id)
