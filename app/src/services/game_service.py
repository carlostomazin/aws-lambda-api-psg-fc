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
        game = self.repository.get({"id": game_id})
        if not game:
            return None
        game = game[0]

        # Adiciona os totais de jogadores e valores pagos
        return self._get_game_with_totals(game)

    def get_game_by_date(self, game_date: date) -> dict | None:
        game_date = game_date.isoformat()
        game = self.repository.get({"game_date": game_date})
        if not game:
            return None
        game = game[0]

        # Adiciona os totais de jogadores e valores pagos
        return self._get_game_with_totals(game)

    def get_games(self) -> list[dict]:
        games = self.repository.get()
        if not games:
            return []

        # Adiciona os totais de jogadores e valores pagos
        return [self._get_game_with_totals(game) for game in games]

    def delete_game(self, game_id: str) -> None:
        return self.repository.delete(game_id)

    def _get_game_with_totals(self, game: dict) -> dict:
        from src.services.game_player_service import GamePlayerService

        gp_service = GamePlayerService()
        players = gp_service.get_players_in_game(game["id"]) or []
        players_total = len(players) if players else 0
        players_paid = sum(1 for player in players if player["amount_paid"] and player["amount_paid"] > 0)
        players_visitors = sum(1 for player in players if player["is_visitor"])
        total_amount = sum(player["amount_paid"] for player in players if player["amount_paid"])

        game["players_total"] = players_total
        game["players_paid"] = players_paid
        game["total_amount"] = total_amount
        game["players_visitors"] = players_visitors

        return game
