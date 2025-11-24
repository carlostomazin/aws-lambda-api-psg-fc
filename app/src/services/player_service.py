from fastapi import HTTPException
from src.repositories import PlayerRepository
from src.schemas import PlayerResponse


class PlayerService:
    def __init__(self):
        self.repository = PlayerRepository()

    def resolve_or_create_player(self, name: str) -> PlayerResponse:
        name_clean = name.strip()

        resp = self.repository.get_by_name(name_clean)

        if resp:
            return PlayerResponse.model_validate(resp)

        insert_resp = self.repository.create(name_clean)

        if not insert_resp:
            raise HTTPException(status_code=500, detail="Erro ao criar jogador")

        return PlayerResponse.model_validate(insert_resp)
