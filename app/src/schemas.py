from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel


# -------------------------------------------------------------------
# games
# -------------------------------------------------------------------



class GameResponse(BaseModel):
    id: str
    created_at: str
    updated_at: Optional[str]
    game_date: date
    players_total: int
    players_paid: int
    players_visitors: int
    total_amount: float
    game_price: float
    price_per_player: float


class GameUpdate(BaseModel):
    game_date: date = None
    game_price: float = None
    price_per_player: float = None
    goalkeepers_pay: bool = None


# -------------------------------------------------------------------
# players
# -------------------------------------------------------------------
class PlayerResponse(BaseModel):
    id: str
    created_at: str
    updated_at: Optional[str]
    name: str


# -------------------------------------------------------------------
# games/players
# -------------------------------------------------------------------
class GamePlayerTeamResponse(BaseModel):
    id: str
    created_at: str
    updated_at: Optional[str]
    is_goalkeeper: bool
    is_visitor: bool
    paid: bool
    team: Optional[str]
    player: PlayerResponse
    player_invited: Optional[PlayerResponse]


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
    teams: Dict[str, List[GamePlayerTeamResponse]]
