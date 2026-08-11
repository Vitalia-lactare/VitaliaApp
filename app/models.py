from datetime import date
from typing import Optional

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
