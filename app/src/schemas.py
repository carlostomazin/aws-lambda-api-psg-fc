from datetime import date, datetime, time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# games
# -------------------------------------------------------------------
class GameRequest(BaseModel):
    game_date: date


class GameResponse(BaseModel):
    id: str
    created_at: str
    updated_at: Optional[str]
    game_date: date
    players_total: int
    players_paid: int
    players_visitors: int


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
class GamePlayerRequest(BaseModel):
    name: str
    is_goalkeeper: bool = False
    is_visitor: bool = False
    paid: bool = False
    invited_by: Optional[str] = None
    team: Optional[str] = None


class GamePlayerUpdate(BaseModel):
    updated_at: time = datetime.now()
    is_goalkeeper: Optional[bool] = None
    is_visitor: Optional[bool] = None
    paid: Optional[bool] = None
    invited_by: Optional[str] = None
    team: Optional[str] = None


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
