from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class GameRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def update(self, game_id: str, payload: dict) -> dict | None:
        """Update data in Supabase"""
        response = (
            self.supabase.table("games").update(payload).eq("id", game_id).execute()
        )
        if response.data:
            return response.data[0]
        return None

    def get_by_id(self, game_id: str) -> dict | None:
        """Get game by ID from Supabase"""
        response = (
            self.supabase.table("games").select("*").eq("id", game_id).execute()
        )
        if response.data:
            return response.data[0]
        return None

    def get_by_date(self, game_date: str) -> dict | None:
        """Get game by date from Supabase"""
        response = (
            self.supabase.table("games")
            .select("*")
            .eq("game_date", game_date)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    def create(self, payload: dict) -> dict | None:
        """Create new game in Supabase"""
        response = self.supabase.table("games").insert(payload).execute()
        if response.data:
            return response.data[0]
        return None