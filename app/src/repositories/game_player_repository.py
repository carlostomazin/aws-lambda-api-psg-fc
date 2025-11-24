import os

from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class GamePlayerRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def upsert(self, data) -> dict:
        resp = (
            self.supabase.table("game_players")
            .upsert(data, on_conflict="game_id,player_id")
            .execute()
        )

        if not resp.data:
            return None

        return resp.data[0]
