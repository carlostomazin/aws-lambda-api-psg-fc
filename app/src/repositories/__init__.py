import os

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

from .game_player_repository import GamePlayerRepository
from .player_repository import PlayerRepository

__all__ = ["PlayerRepository", "GamePlayerRepository"]
