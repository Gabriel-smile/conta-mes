from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Gasto:
    descricao: str
    valor: Decimal
    categoria: str
    data: date
    id: int | None = None

    def __post_init__(self):
        self.descricao = self.descricao.strip()
        self.categoria = self.categoria.strip().lower()
        if self.valor <= 0:
            raise ValueError("valor tem que ser maior que zero")
        if not self.descricao:
            raise ValueError("descrição não pode ser vazia")
        if not self.categoria:
            raise ValueError("categoria não pode ser vazia")
