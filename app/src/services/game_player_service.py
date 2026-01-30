from typing import Optional

from pydantic import BaseModel
from src.repositories import GamePlayerRepository


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

    def add_player_in_game(self, game_id: str, data: GamePlayerAddSchema):
        # Regras de negócio
        if data.paid is True and data.amount_paid is None:
            raise Exception("Para marcar o jogador como pago, é necessário informar o valor pago.")

        if data.is_visitor is True and data.invited_by is None:
            raise Exception("O jogador visitante deve ter um convidador.")

        # Preparar os dados para inserção
        from src.services.player_service import PlayerService

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

    def update_player_in_game(self, game_id, player_id, data: GamePlayerUpdateSchema):
        print("update_player_in_game", data)
        # Regras de negócio
        from src.services.game_service import GameService

        game = GameService().get_game(game_id)

        if data.paid is True and data.amount_paid is None and game["price_per_player"] is None:
            raise Exception(
                "Para marcar o jogador como pago, é necessário informar o valor pago ou ter um preço por jogador definido no jogo."
            )

        if data.is_visitor is True and data.invited_by is None:
            raise Exception("O jogador visitante deve ter um convidador.")

        if data.paid is True:
            player = self.get_player_in_game(game_id, player_id)
            if data.is_goalkeeper is True or player["is_goalkeeper"] is True:
                if game["goalkeepers_pay"] is False:
                    data.amount_paid = 0.0
                else:
                    if game["price_per_player"] is not None:
                        data.amount_paid = game["price_per_player"]
            elif data.amount_paid == 0.0:
                if game["price_per_player"] is not None:
                    print("Setting amount_paid to price_per_player:", game["price_per_player"])
                    data.amount_paid = game["price_per_player"]

        # Prepara os dados para atualização
        update_data = {}

        if data.is_goalkeeper is not None:
            update_data["is_goalkeeper"] = data.is_goalkeeper
        if data.is_visitor is not None:
            update_data["is_visitor"] = data.is_visitor
        if data.invited_by is not None:
            from src.services.player_service import PlayerService

            player_service = PlayerService()
            update_data["invited_by"] = player_service.get_or_create_player(data.invited_by).id
        if data.paid is not None:
            update_data["paid"] = data.paid
        if data.amount_paid is not None:
            update_data["amount_paid"] = data.amount_paid if data.paid else 0.0
        if data.team is not None:
            update_data["team"] = data.team

        print("update_data", update_data)
        return self.repository.update(game_id, player_id, update_data)

    def get_player_in_game(self, game_id: str, player_id: str) -> Optional[dict]:
        palyer = self.repository.get({"game_id": game_id, "player_id": player_id})
        if not palyer:
            return None
        return palyer[0]

    def get_players_in_game(self, game_id: str):
        return self.repository.get_players(game_id)

    def delete_player_in_game(self, game_id, player_id):
        return self.repository.delete(game_id, player_id)
