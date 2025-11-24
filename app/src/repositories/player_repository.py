from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class PlayerRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_all(self) -> list[dict] | None:
        response = self.supabase.table("players").select("*").order("name").execute()
        if response.data:
            return response.data
        return None

    def get_by_id(self, player_id: str) -> dict | None:
        response = (
            self.supabase.table("players").select("*").eq("id", player_id).execute()
        )
        if response.data:
            return response.data[0]
        return None

    def get_by_name(self, player_name: str) -> dict | None:
        response = (
            self.supabase.table("players")
            .select("*")
            .ilike("name", player_name)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]
        return None

    def create(self, name: str) -> dict | None:
        payload = {"name": name}
        response = self.supabase.table("players").insert(payload).execute()
        if response.data:
            return response.data[0]
        return None

    def update(self, player_id: str, payload: dict) -> dict | None:
        """Update player data in Supabase"""
        response = (
            self.supabase.table("players").update(payload).eq("id", player_id).execute()
        )
        if response.data:
            return response.data[0]
        return None

    def delete(self, player_id: str) -> list[dict]:
        response = self.supabase.table("players").delete().eq("id", player_id).execute()
        return response.data
