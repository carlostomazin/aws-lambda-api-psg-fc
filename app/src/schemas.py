from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel


# -------------------------------------------------------------------
# games/teams
# -------------------------------------------------------------------
class GenerateTeamsRequest(BaseModel):
    jogadores_raw: str
    zagueiros_fixos: List[str]
    habilidosos: List[str]
    players_per_team: Optional[int] = 6


class GenerateTeamsResponse(BaseModel):
    game_id: str
    teams: Dict[str, List[Dict]]
