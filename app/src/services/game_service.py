from datetime import date
from typing import Optional

from pydantic import BaseModel
from src.repositories import GameRepository
from src.services import GamePlayerService


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
        self.game_player_service = GamePlayerService()

    def get_or_create_game(self, body: GameAddSchema) -> dict | None:
        game = self.get_game_by_date(body.game_date)
        if game:
            return game

        body.game_date = body.game_date.isoformat()

        return self.repository.create(body.model_dump())

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

    def get_game(self, game_id: str) -> dict | None:
        result = self.repository.get({"id": game_id})
        return result[0] if result else None

    def get_game_by_date(self, game_date: date) -> dict | None:
        game_date = game_date.isoformat()
        result = self.repository.get({"game_date": game_date})
        return result[0] if result else None

    def get_games(self) -> list[dict]:
        games = self.repository.get()
        games_with_total = []
        for game in games:
            players = self.game_player_service.get_players_in_game(game["id"])
            if players is None:
                players = []
            players_total = len(players) if players else 0
            players_paid = sum(1 for player in players if player["amount_paid"] and player["amount_paid"] > 0)
            players_visitors = sum(1 for player in players if player["is_visitor"])
            total_amount = sum(player["amount_paid"] for player in players if player["amount_paid"])

            game["players_total"] = players_total
            game["players_paid"] = players_paid
            game["total_amount"] = total_amount
            game["players_visitors"] = players_visitors

            games_with_total.append(game)

        return games_with_total

    def delete_game(self, game_id: str) -> None:
        return self.repository.delete(game_id)
