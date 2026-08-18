from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, constr


class DoadoraIn(BaseModel):
    nome: str = Field(min_length=2)
    email: EmailStr
    telefone: str = Field(min_length=8)
    cidade: str = Field(min_length=2)
    uf: constr(min_length=2, max_length=2)
    bebe_nascimento: Optional[date] = None
    ja_doou_antes: bool = False
    mensagem: Optional[str] = None
    banco_leite_id: Optional[int] = None


class ContatoIn(BaseModel):
    nome: str = Field(min_length=2)
    email: EmailStr
    assunto: Optional[str] = None
    mensagem: str = Field(min_length=3)


class CampanhaIn(BaseModel):
    titulo: str = Field(min_length=2)
    resumo: str = Field(min_length=2)
    conteudo: Optional[str] = None
    imagem_url: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None


class TriagemIn(BaseModel):
    sessao_id: constr(min_length=8)
    amamentando: Literal["sim_atualmente", "ainda_nao", "nao_mais"]
    idade_bebe: Literal[
        "menos_1_mes", "1_a_3_meses", "3_a_6_meses",
        "6_a_12_meses", "mais_12_meses", "nao_se_aplica",
    ]
    usa_medicamento: bool
    fumante: bool
    exame_recente: bool
    ja_doou_antes: bool


class EventoIn(BaseModel):
    sessao_id: constr(min_length=8)
    evento: constr(min_length=2)
    etapa: Optional[str] = None
    metadata: Optional[dict] = None


class CadastroPortalIn(DoadoraIn):
    sessao_id: constr(min_length=8)
    cep: constr(min_length=8, max_length=9)


class AgendamentoIn(BaseModel):
    doadora_id: int
    sessao_id: constr(min_length=8)
    endereco_coleta: str = Field(min_length=3)
    data_preferida: Optional[date] = None
    periodo: Optional[Literal["manha", "tarde", "noite"]] = None


class FeedbackIn(BaseModel):
    doadora_id: int
    sessao_id: constr(min_length=8)
    nota: int = Field(ge=1, le=5)
    comentario: Optional[str] = None


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatIn(BaseModel):
    mensagem: str = Field(min_length=1, max_length=1000)
    historico: list[ChatMessageIn] = Field(default_factory=list, max_length=20)
