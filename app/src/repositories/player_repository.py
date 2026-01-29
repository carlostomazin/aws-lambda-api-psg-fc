from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class PlayerRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def create(self, body: dict) -> dict | None:
        response = self.supabase.table("players").insert(body).execute()
        if response.data:
            return response.data[0]
        return None

    def update(self, player_id: str, body: dict) -> dict | None:
        """Update player data in Supabase"""
        response = self.supabase.table("players").update(body).eq("id", player_id).execute()
        if response.data:
            return response.data[0]
        return None

    def get(self, filters: dict | None = None) -> list[dict] | None:
        query = self.supabase.table("players").select("*")

        if filters:
            for field, value in filters.items():
                if value is None:
                    continue  # ignora filtros vazios

                # se vier lista/tupla, vira IN
                if isinstance(value, (list, tuple, set)):
                    query = query.in_(field, list(value))
                else:
                    query = query.eq(field, value)

        # order
        query = query.order("name")

        response = query.execute()
        return response.data or None

    def delete(self, player_id: str) -> None:
        self.supabase.table("players").delete().eq("id", player_id).execute()
        return None
