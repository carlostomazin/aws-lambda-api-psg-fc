from typing import Dict

from fastapi import HTTPException
from src.repositories import GameRepository

class ExceptionGameNotFound(HTTPException):
    pass

class GameService:
    def __init__(self):
        self.repository = GameRepository()

    def update_game(self, game_id: str, payload: Dict[str, object]) -> dict | None:
        resp = self.repository.update(game_id, payload)
        if resp:
            return resp
        raise HTTPException(404, "Registro não encontrado")

    def get_game_by_id(self, game_id: str) -> dict | None:
        return self.repository.get_by_id(game_id)
