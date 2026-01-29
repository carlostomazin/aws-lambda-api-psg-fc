from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class GameRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def update(self, game_id: str, body: dict) -> dict | None:
        """Update data in Supabase"""
        response = self.supabase.table("games").update(body).eq("id", game_id).execute()
        if response.data:
            return response.data[0]
        return None

    def get_by_id(self, game_id: str) -> dict | None:
        """Get game by ID from Supabase"""
        response = self.supabase.table("games").select("*").eq("id", game_id).execute()
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

    def get_all(self) -> list[dict]:
        """Get all games from Supabase"""
        response = self.supabase.table("games").select("*").execute()
        return response.data

    def create(self, body: dict) -> dict | None:
        """Create new game in Supabase"""
        response = self.supabase.table("games").insert(body).execute()
        if response.data:
            return response.data[0]
        return None

    def delete(self, game_id: str) -> None:
        """Delete game by ID from Supabase"""
        self.supabase.table("games").delete().eq("id", game_id).execute()
        return None
