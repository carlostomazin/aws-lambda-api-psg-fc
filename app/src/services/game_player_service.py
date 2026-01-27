from typing import Optional

from pydantic import BaseModel
from src.repositories import GamePlayerRepository
from src.schemas import GamePlayerTeamResponse
from src.services.game_service import ExceptionGameNotFound, GameService
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

    def update_player_in_game(self, game_id, player_id, data: GamePlayerUpdateSchema):
        player_service = PlayerService()

        # Recupera ou cria o jogador que convidou, se aplicável
        invited_by_id = None
        if data.is_visitor is True:
            if data.invited_by:
                invited_by_id = player_service.resolve_or_create_player(
                    data.invited_by
                ).id
            else:
                raise Exception("O jogador visitante deve ter um convidador.")
        
        # Prepara os dados para atualização
        update_data = {}

        if data.is_goalkeeper is not None:
            update_data["is_goalkeeper"] = data.is_goalkeeper
        if data.is_visitor is not None:
            update_data["is_visitor"] = data.is_visitor
        if invited_by_id is not None or data.invited_by is not None:
            update_data["invited_by"] = invited_by_id
        if data.paid is not None:
            update_data["paid"] = data.paid
        if data.amount_paid is not None:
            update_data["amount_paid"] = data.amount_paid
        if data.team is not None:
            update_data["team"] = data.team

        return self.repository.update(game_id, player_id, update_data)

    def add_player_in_game(self, game_id: str, data: GamePlayerAddSchema):
        # Validar se o game_id existe
        game_service = GameService()
        if not game_service.get_game_by_id(game_id):
            raise ExceptionGameNotFound

        # Recupera ou cria o jogador
        player_service = PlayerService()
        player_id = player_service.resolve_or_create_player(data.name).id

        # Recupera ou cria o jogador que convidou, se aplicável
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
