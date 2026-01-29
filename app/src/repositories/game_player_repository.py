import os

from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class GamePlayerRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get(self, filters: dict | None = None) -> list[dict] | None:
        query = self.supabase.table("game_players").select("*")

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
    
    def get_games(self, player_id: str) -> list[dict] | None:
        response = (
            self.supabase.table("game_players")
            .select("game:game_id (*)")
            .eq("player_id", player_id)
            .execute()
        )
        if response.data:
            return [item["game"] for item in response.data]
        return None

    def get_players(self, game_id: str) -> list[dict] | None:
        response = (
            self.supabase.table("game_players")
            .select(
                "id, created_at, updated_at, is_goalkeeper, is_visitor, paid, amount_paid, team, player:player_id (*), player_invited:invited_by (*)"
            )
            .eq("game_id", game_id)
            .execute()
        )
        if response.data:
            return response.data
        return None

    def upsert(self, data) -> dict:
        resp = (
            self.supabase.table("game_players")
            .upsert(data, on_conflict="game_id,player_id")
            .execute()
        )

        if not resp.data:
            return None

        return resp.data[0]

    def delete(self, game_id: str, player_id: str):
        response = (
            self.supabase.table("game_players")
            .delete()
            .eq("game_id", game_id)
            .eq("player_id", player_id)
            .execute()
        )
        return response.data

    def update(self, game_id, player_id, body):
        response = (
            self.supabase.table("game_players")
            .update(body)
            .eq("game_id", game_id)
            .eq("player_id", player_id)
            .execute()
        )
        if response.data:
            return response.data[0]
        return
