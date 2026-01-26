import os

from src.repositories import SUPABASE_KEY, SUPABASE_URL
from supabase import Client, create_client


class GamePlayerRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_by_player_id(self, player_id: str) -> dict | None:
        response = (
            self.supabase.table("game_players")
            .select("*")
            .eq("player_id", player_id)
            .execute()
        )
        if response.data:
            return response.data[0]
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

    def update(self, game_id, player_id, payload):
        response = (
            self.supabase.table("game_players")
            .update(payload)
            .eq("game_id", game_id)
            .eq("player_id", player_id)
            .execute()
        )
        if response.data:
            return response.data[0]
        return
