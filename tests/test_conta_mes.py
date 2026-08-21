import csv
import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from conta_mes.db import inserir, listar, remover, total_por_categoria
from conta_mes.models import Gasto
from conta_mes.reports import exportar_csv, parse_data, resumo_mensal


@pytest.fixture
def db_tmp(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


def _gasto(**kwargs) -> Gasto:
    defaults = {
        "descricao": "mercado",
        "valor": Decimal("120.50"),
        "categoria": "alimentacao",
        "data": date(2025, 8, 10),
    }
    defaults.update(kwargs)
    return Gasto(**defaults)


def test_inserir_e_listar(db_tmp: Path):
    gid = inserir(_gasto(), db_tmp)
    assert gid == 1

    gastos = listar(db_tmp, mes=8, ano=2025)
    assert len(gastos) == 1
    assert gastos[0].descricao == "mercado"
    assert gastos[0].valor == Decimal("120.50")


def test_filtro_categoria(db_tmp: Path):
    inserir(_gasto(categoria="transporte", descricao="uber"), db_tmp)
    inserir(_gasto(descricao="ifood"), db_tmp)

    alimentacao = listar(db_tmp, categoria="alimentacao")
    assert len(alimentacao) == 1
    assert alimentacao[0].descricao == "ifood"


def test_filtro_mes_sem_ano(db_tmp: Path):
    inserir(_gasto(data=date(2024, 8, 5), descricao="agosto 2024"), db_tmp)
    inserir(_gasto(data=date(2025, 8, 10), descricao="agosto 2025"), db_tmp)
    inserir(_gasto(data=date(2025, 7, 15), descricao="julho 2025"), db_tmp)

    agosto = listar(db_tmp, mes=8)
    assert len(agosto) == 2
    assert {g.descricao for g in agosto} == {"agosto 2024", "agosto 2025"}


def test_valor_decimal_preservado(db_tmp: Path):
    inserir(_gasto(valor=Decimal("10.05")), db_tmp)
    gastos = listar(db_tmp)
    assert gastos[0].valor == Decimal("10.05")


def test_migracao_valor_real(db_tmp: Path):
    with sqlite3.connect(db_tmp) as conn:
        conn.execute(
            """
            CREATE TABLE gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                categoria TEXT NOT NULL,
                data TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO gastos (descricao, valor, categoria, data) VALUES (?, ?, ?, ?)",
            ("legado", 99.99, "outros", "2025-08-01"),
        )

    gastos = listar(db_tmp)
    assert len(gastos) == 1
    assert gastos[0].valor == Decimal("99.99")


def test_total_por_categoria(db_tmp: Path):
    inserir(_gasto(valor=Decimal("100")), db_tmp)
    inserir(_gasto(valor=Decimal("50"), descricao="padaria"), db_tmp)
    inserir(_gasto(valor=Decimal("30"), categoria="transporte", descricao="onibus"), db_tmp)

    totais = total_por_categoria(db_tmp, mes=8, ano=2025)
    assert totais["alimentacao"] == Decimal("150")
    assert totais["transporte"] == Decimal("30")


def test_remover(db_tmp: Path):
    gid = inserir(_gasto(), db_tmp)
    assert remover(gid, db_tmp) is True
    assert listar(db_tmp) == []


def test_gasto_validacao():
    with pytest.raises(ValueError):
        Gasto(descricao="", valor=Decimal("1"), categoria="outros", data=date.today())

    with pytest.raises(ValueError):
        Gasto(descricao="x", valor=Decimal("0"), categoria="outros", data=date.today())


def test_parse_data():
    assert parse_data("2025-08-21") == date(2025, 8, 21)
    assert parse_data("21/08/2025") == date(2025, 8, 21)


def test_exportar_csv(db_tmp: Path, tmp_path: Path):
    inserir(_gasto(), db_tmp)
    destino = tmp_path / "saida.csv"
    qtd = exportar_csv(destino, db_tmp, mes=8, ano=2025)
    assert qtd == 1

    with destino.open(encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["id", "data", "descricao", "categoria", "valor"]
    assert rows[1][2] == "mercado"


def test_resumo_mensal(db_tmp: Path):
    inserir(_gasto(valor=Decimal("80")), db_tmp)
    inserir(_gasto(valor=Decimal("20"), categoria="lazer", descricao="cinema"), db_tmp)

    texto = resumo_mensal(8, 2025, db_tmp)
    assert "alimentacao" in texto
    assert "TOTAL" in texto
