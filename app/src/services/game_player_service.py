from typing import Optional

from pydantic import BaseModel
from src.repositories import GamePlayerRepository
from src.services.player_service import PlayerService


class GamePlayerAddSchema(BaseModel):
    name: str
    is_goalkeeper: Optional[bool] = False
    is_visitor: Optional[bool] = False
    invited_by: Optional[str] = None
    paid: Optional[bool] = False
    amount_paid: Optional[float] = None
    team: Optional[str] = None


class GamePlayerUpdateSchema(BaseModel):
    is_goalkeeper: Optional[bool] = None
    is_visitor: Optional[bool] = None
    invited_by: Optional[str] = None
    paid: Optional[bool] = None
    amount_paid: Optional[float] = None
    team: Optional[str] = None


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
    ):
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

    # def create_or_update_game_player(self, data:

    def delete_player_in_game(self, game_id, player_id):
        return self.repository.delete(game_id, player_id)

    def get_players_in_game(self, game_id: str):
        return self.repository.get_players(game_id)

    def update_player_in_game(self, game_id, player_id, data: GamePlayerUpdateSchema):
        # Regras de negócio
        if data.paid is True and data.amount_paid is None:
            raise Exception("O valor pago deve ser informado quando o jogador for marcado como pago.")
        else:
            pass

        if data.is_visitor is True and data.invited_by is None:
            raise Exception("O jogador visitante deve ter um convidador.")

        # Prepara os dados para atualização
        player_service = PlayerService()
        update_data = {}

        if data.is_goalkeeper:
            update_data["is_goalkeeper"] = data.is_goalkeeper
        if data.is_visitor:
            update_data["is_visitor"] = data.is_visitor
        if data.invited_by:
            update_data["invited_by"] = player_service.get_or_create_player(data.invited_by).id
        if data.paid:
            update_data["paid"] = data.paid
        if data.amount_paid:
            update_data["amount_paid"] = data.amount_paid
        if data.team:
            update_data["team"] = data.team

        return self.repository.update(game_id, player_id, update_data)

    def add_player_in_game(self, game_id: str, data: GamePlayerAddSchema):
        # Regras de negócio
        if data.paid is True and data.amount_paid is None:
            raise Exception("O valor pago deve ser informado quando o jogador for marcado como pago.")

        if data.is_visitor is True and data.invited_by is None:
            raise Exception("O jogador visitante deve ter um convidador.")

        # Preparar os dados para inserção
        player_service = PlayerService()

        add_data = {
            "game_id": game_id,
            "player_id": player_service.get_or_create_player(data.name).id,
            "is_goalkeeper": data.is_goalkeeper,
            "is_visitor": data.is_visitor,
            "invited_by": (player_service.get_or_create_player(data.invited_by).id if data.invited_by else None),
            "paid": data.paid,
            "amount_paid": data.amount_paid,
            "team": data.team,
        }

        self.repository.upsert(add_data)
