import random
import re

from emoji import replace_emoji
from src.utils import normalize_name


class GameTeamService:
    def __init__(self):
        pass

    def parse_jogadores_raw(self, jogadores_raw: str) -> dict:
        """
        Faz o parse do texto bruto da lista de jogadores (copiado do WhatsApp, por exemplo)
        e retorna uma lista de jogadores estruturada em dicionários.

        Parameters:
            jogadores_raw(str): Texto bruto contendo a lista de jogadores e seções.

        Returns:
            list[dict]: Lista de dicionários de jogadores no formato:
            {
                "name": str,
                "invited_by_name": str | None,
                "is_goalkeeper": bool,
                "is_visitor": bool
            }
        """
        jogadores_raw = replace_emoji(jogadores_raw, replace="")

        lines = jogadores_raw.splitlines()
        section = None
        players = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "GOLEIROS" in line.upper():
                section = "goleiros"
                continue
            if "DA CASA" in line.upper():
                section = "casa"
                continue
            if "VISITANTES" in line.upper():
                section = "visitantes"
                continue
            if "NÃO VÃO" in line.upper() or "NAO VAO" in line.upper():
                section = "nao_vao"
                continue

            m = re.match(r"^\d+\.\s*(.+)$", line)
            if not m or section is None:
                continue

            raw = m.group(1).strip()
            if not raw or raw == ".":
                continue

            paren = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", raw)
            invited_by_name = None
            name_part = raw
            if paren:
                name_part = paren.group(1).strip()
                invited_by_name = paren.group(2).strip()

            if section == "nao_vao":
                continue

            is_goalkeeper = section == "goleiros"
            is_visitor = (section == "visitantes") or (
                section == "goleiros" and invited_by_name is not None
            )

            players.append(
                {
                    "name": normalize_name(name_part),
                    "invited_by_name": (
                        normalize_name(invited_by_name) if invited_by_name else None
                    ),
                    "is_goalkeeper": is_goalkeeper,
                    "is_visitor": is_visitor,
                }
            )

        return players

    def generate_teams(
        self, players, zagueiros_fixos, habilidosos, players_per_team: int = 6
    ):
        defenders = []
        skilled = []
        others = []

        goalkeepers = [dict(p) for p in players if p["is_goalkeeper"] is True]
        players = [dict(j) for j in players if j["is_goalkeeper"] is False]

        if players_per_team == None:
            players_per_team = 6

        for p in players:
            n = p["name"]
            if n in zagueiros_fixos:
                defenders.append(p)
            elif n in habilidosos:
                skilled.append(p)
            else:
                others.append(p)

        # Embaralha tudo pra ficar aleatório
        random.shuffle(defenders)
        random.shuffle(skilled)
        random.shuffle(others)

        # Times iniciais (A, B, ...)
        team_keys = [chr(ord("A") + i) for i in range(2)]
        teams = {k: [] for k in team_keys}

        # ---------------------------------
        # Helper pra adicionar jogador
        # - respeita players_per_team
        # - só cria novo time se TODOS os times atuais estiverem cheios
        # ---------------------------------
        def add_player(player, preferred_key: str | None = None):
            nonlocal team_keys, teams

            # Se não tem limite definido, só joga no preferred ou aleatório
            if players_per_team is None:
                key = (
                    preferred_key
                    if preferred_key is not None
                    else random.choice(team_keys)
                )
                teams[key].append(player)
                return

            # 1) Se tem preferred_key e ele ainda não está cheio, usa ele
            if (
                preferred_key is not None
                and len(teams[preferred_key]) < players_per_team
            ):
                teams[preferred_key].append(player)
                return

            # 2) Procura algum time com vaga
            available = [k for k in team_keys if len(teams[k]) < players_per_team]
            if available:
                key = random.choice(available)
                teams[key].append(player)
                return

            # 3) Se chegou aqui, TODOS os times estão cheios
            #    -> cria um novo time e coloca o jogador nele
            new_key = chr(ord(team_keys[-1]) + 1)
            team_keys.append(new_key)
            teams[new_key] = []
            teams[new_key].append(player)

        # ---------------------------
        # 1) Distribuir zagueiros
        # Regra: tentar pelo menos 1 por time, se possível
        # ---------------------------
        d_index = 0

        if len(defenders) >= len(team_keys):
            # 1 zagueiro por time
            for key in list(team_keys):
                if d_index >= len(defenders):
                    break
                add_player(defenders[d_index], preferred_key=key)
                d_index += 1
        else:
            # menos zagueiros que times: distribui o que der
            for key in list(team_keys):
                if d_index >= len(defenders):
                    break
                add_player(defenders[d_index], preferred_key=key)
                d_index += 1

        # Zagueiros restantes
        for d in defenders[d_index:]:
            add_player(d)

        # ---------------------------
        # 2) Distribuir habilidosos
        # Regra: tentar 1 e depois 2 por time (se possível)
        # ---------------------------
        s_index = 0
        total_skilled = len(skilled)

        # 1 por time
        if total_skilled >= len(team_keys):
            for key in list(team_keys):
                if s_index >= total_skilled:
                    break
                add_player(skilled[s_index], preferred_key=key)
                s_index += 1
        else:
            for key in list(team_keys):
                if s_index >= total_skilled:
                    break
                add_player(skilled[s_index], preferred_key=key)
                s_index += 1

        # 2 por time (se sobrar)
        if total_skilled - s_index >= len(team_keys):
            for key in list(team_keys):
                if s_index >= total_skilled:
                    break
                add_player(skilled[s_index], preferred_key=key)
                s_index += 1

        # Habilidosos restantes
        for s in skilled[s_index:]:
            add_player(s)

        # ---------------------------
        # 3) Distribuir o resto (others)
        # ---------------------------
        for o in others:
            add_player(o)

        # ---------------------------
        # 4) Setar o campo "team"
        # ---------------------------
        all_players = []
        for key, players in teams.items():
            for p in players:
                p["team"] = key
            all_players.extend(all_players)

        for g in goalkeepers:
            g["team"] = None
            all_players.append(g)

        return all_players
