import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import Gasto

DEFAULT_DB = Path.home() / ".conta_mes" / "gastos.db"

CATEGORIAS_PADRAO = (
    "alimentacao",
    "transporte",
    "moradia",
    "lazer",
    "saude",
    "outros",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor TEXT NOT NULL,
    categoria TEXT NOT NULL,
    data TEXT NOT NULL
)
"""


def _connect(caminho: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    return conn


def _coluna_valor_e_real(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("PRAGMA table_info(gastos)").fetchall()
    for row in rows:
        if row["name"] == "valor":
            return row["type"].upper() == "REAL"
    return False


def _migrar_valor_real_para_text(conn: sqlite3.Connection) -> None:
    if not _coluna_valor_e_real(conn):
        return

    conn.executescript(
        """
        CREATE TABLE gastos_nova (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor TEXT NOT NULL,
            categoria TEXT NOT NULL,
            data TEXT NOT NULL
        );
        INSERT INTO gastos_nova (id, descricao, valor, categoria, data)
        SELECT id, descricao, valor, categoria, data FROM gastos;
        DROP TABLE gastos;
        ALTER TABLE gastos_nova RENAME TO gastos;
        """
    )

    for row in conn.execute("SELECT id, valor FROM gastos").fetchall():
        texto = format(Decimal(str(row["valor"])), "f")
        conn.execute("UPDATE gastos SET valor = ? WHERE id = ?", (texto, row["id"]))


def init_db(caminho: Path = DEFAULT_DB) -> None:
    with _connect(caminho) as conn:
        conn.execute(_SCHEMA)
        _migrar_valor_real_para_text(conn)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_gastos_data ON gastos(data)"
        )


def inserir(gasto: Gasto, caminho: Path = DEFAULT_DB) -> int:
    init_db(caminho)
    with _connect(caminho) as conn:
        cur = conn.execute(
            """
            INSERT INTO gastos (descricao, valor, categoria, data)
            VALUES (?, ?, ?, ?)
            """,
            (
                gasto.descricao,
                format(gasto.valor, "f"),
                gasto.categoria,
                gasto.data.isoformat(),
            ),
        )
        return cur.lastrowid


def listar(
    caminho: Path = DEFAULT_DB,
    mes: int | None = None,
    ano: int | None = None,
    categoria: str | None = None,
) -> list[Gasto]:
    init_db(caminho)
    query = "SELECT id, descricao, valor, categoria, data FROM gastos WHERE 1=1"
    params: list = []

    if mes is not None and ano is not None:
        query += " AND data LIKE ?"
        params.append(f"{ano:04d}-{mes:02d}-%")
    elif ano is not None:
        query += " AND data LIKE ?"
        params.append(f"{ano:04d}-%")
    elif mes is not None:
        query += " AND data LIKE ?"
        params.append(f"%-{mes:02d}-%")

    if categoria:
        query += " AND categoria = ?"
        params.append(categoria.lower())

    query += " ORDER BY data DESC, id DESC"

    with _connect(caminho) as conn:
        rows = conn.execute(query, params).fetchall()

    return [
        Gasto(
            id=row["id"],
            descricao=row["descricao"],
            valor=Decimal(row["valor"]),
            categoria=row["categoria"],
            data=date.fromisoformat(row["data"]),
        )
        for row in rows
    ]


def total_por_categoria(
    caminho: Path = DEFAULT_DB,
    mes: int | None = None,
    ano: int | None = None,
) -> dict[str, Decimal]:
    gastos = listar(caminho, mes=mes, ano=ano)
    totais: dict[str, Decimal] = {}
    for g in gastos:
        totais[g.categoria] = totais.get(g.categoria, Decimal("0")) + g.valor
    return dict(sorted(totais.items(), key=lambda x: x[1], reverse=True))


def remover(gasto_id: int, caminho: Path = DEFAULT_DB) -> bool:
    init_db(caminho)
    with _connect(caminho) as conn:
        cur = conn.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        return cur.rowcount > 0
