from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GameCreate(BaseModel):
    game_date: date = Field(..., description="Data do jogo (YYYY-MM-DD)")


class GameOut(BaseModel):
    id: str
    game_date: date
    players_total: int
    players_paid: int
    players_visitors: int


class GenerateTeamsRequest(BaseModel):
    jogadores_raw: str = Field(
        ...,
        examples=[
            "\n🏟 Futebol Segunda - 20h\n📍 Society Hidrofit\n💰 R$ 12,00 por jogador\n📲 Pix (chave aleatória): 40165266-dfa1-4e35-ae05-efdf2b5b8a6e\n👤 Carlos Augusto \n\n⚠ CONFIRMAÇÃO OBRIGATÓRIA ATÉ 12H DE SEGUNDA PARA OS DA CASA ⚠\nApós esse horário, abrimos vaga pros visitantes.\n\n🧤 GOLEIROS\n1. Ryan (guilherme)\n2.\n\n🏠 DA CASA\n1. Renan\n2. Gustaa\n3. Johnny\n4. Octávio \n5. Leozin\n6. Nathan \n7. beligui \n8. Igão\n9. Matheus\n10. Kevin\n11. Rodrigo ✅©\n12.\n13.\n14.\n15.\n16.\n17.\n18.\n\n🎟 VISITANTES\n1. vinicius (Guilherme)\n2. Murilo (Octávio)\n3. Kovacs (Octávio)\n4. Xoxolim (Leozin)\n5. Yago (Leozin)\n\n🚫 NÃO VÃO\n* Caio Maia\n* Alex\n* \u2060Rafael\n* Carlos\n* \u2060Jeh bass\n* \u2060Fernando\n* \u2060Yan\n* \u2060Vitinho\n* \u2060Rodrigo\n* Gusin\n"
        ],
    )
    zagueiros_fixos: List[str] = Field(
        default=[], examples=[["rodrigo", "fernando", "leozin"]]
    )
    habilidosos: List[str] = Field(
        default=[],
        examples=[["caio maia", "nathan", "carlos", "alex", "gusta", "renan"]],
    )


class PlayerTeamOut(BaseModel):
    id: str
    name: str
    is_goalkeeper: bool
    is_visitor: bool
    paid: bool
    team: Optional[str]


class GenerateTeamsResponse(BaseModel):
    game_id: str
    teams: Dict[str, List[PlayerTeamOut]]


class GamePlayerCreate(BaseModel):
    name: str
    is_goalkeeper: bool = False
    is_visitor: bool = False
    invited_by: Optional[str] = None
    paid: Optional[bool] = None
    team: Optional[str] = None


class GamePlayerUpdate(BaseModel):
    is_goalkeeper: Optional[bool] = None
    is_visitor: Optional[bool] = None
    invited_by: Optional[str] = None
    paid: Optional[bool] = None
    team: Optional[str] = None
