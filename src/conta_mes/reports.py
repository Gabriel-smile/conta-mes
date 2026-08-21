import csv
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path

from .db import listar, total_por_categoria


def formatar_moeda(valor: Decimal) -> str:
    # formato BR simples, sem depender de locale do sistema
    texto = f"{valor:.2f}".replace(".", ",")
    return f"R$ {texto}"


def resumo_mensal(
    mes: int,
    ano: int,
    caminho: Path,
) -> str:
    totais = total_por_categoria(caminho, mes=mes, ano=ano)
    if not totais:
        return f"Nenhum gasto em {mes:02d}/{ano}."

    total_geral = sum(totais.values(), Decimal("0"))
    linhas = [f"Resumo {mes:02d}/{ano}", "-" * 30]

    for cat, valor in totais.items():
        pct = (valor / total_geral * 100) if total_geral else Decimal("0")
        linhas.append(
            f"  {cat:<14} {formatar_moeda(valor):>12}  ({pct:.0f}%)"
        )

    linhas.append("-" * 30)
    linhas.append(f"  {'TOTAL':<14} {formatar_moeda(total_geral):>12}")
    return "\n".join(linhas)


def exportar_csv(
    destino: Path,
    caminho_db: Path,
    mes: int | None = None,
    ano: int | None = None,
) -> int:
    gastos = listar(caminho_db, mes=mes, ano=ano)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "data", "descricao", "categoria", "valor"])
        for g in gastos:
            writer.writerow([
                g.id,
                g.data.isoformat(),
                g.descricao,
                g.categoria,
                f"{g.valor:.2f}",
            ])

    return len(gastos)


def parse_data(texto: str) -> date:
    """Aceita YYYY-MM-DD ou DD/MM/YYYY."""
    texto = texto.strip()
    if "/" in texto:
        dia, mes, ano = texto.split("/")
        return date(int(ano), int(mes), int(dia))
    return date.fromisoformat(texto)
