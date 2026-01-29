from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class GameRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def create(self, body: dict) -> dict | None:
        """Create new game in Supabase"""
        response = self.supabase.table("games").insert(body).execute()
        if response.data:
            return response.data[0]
        return None

    def update(self, game_id: str, body: dict) -> dict | None:
        """Update data in Supabase"""
        response = self.supabase.table("games").update(body).eq("id", game_id).execute()
        if response.data:
            return response.data[0]
        return None

    def get(self, filters: dict | None = None) -> list[dict] | None:
        query = self.supabase.table("games").select("*")

        if filters:
            for field, value in filters.items():
                if value is None:
                    continue  # ignora filtros vazios

                # se vier lista/tupla, vira IN
                if isinstance(value, (list, tuple, set)):
                    query = query.in_(field, list(value))
                else:
                    query = query.eq(field, value)

        response = query.execute()
        return response.data or None

    def delete(self, game_id: str) -> None:
        """Delete game by ID from Supabase"""
        self.supabase.table("games").delete().eq("id", game_id).execute()
        return None
