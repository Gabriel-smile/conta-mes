import argparse
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .db import CATEGORIAS_PADRAO, DEFAULT_DB, inserir, listar, remover
from .models import Gasto
from .reports import exportar_csv, formatar_moeda, parse_data, resumo_mensal


def _parse_valor(texto: str) -> Decimal:
    # aceita "45,90" ou "45.90"
    normalizado = texto.strip().replace(",", ".")
    try:
        return Decimal(normalizado)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"valor inválido: {texto}") from exc


def _db_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"caminho do banco SQLite (padrão: {DEFAULT_DB})",
    )
    return p


def cmd_add(args: argparse.Namespace) -> None:
    gasto = Gasto(
        descricao=args.descricao,
        valor=args.valor,
        categoria=args.categoria,
        data=parse_data(args.data) if args.data else date.today(),
    )
    gid = inserir(gasto, args.db)
    print(f"Gasto #{gid} registrado: {gasto.descricao} ({formatar_moeda(gasto.valor)})")


def cmd_list(args: argparse.Namespace) -> None:
    gastos = listar(args.db, mes=args.mes, ano=args.ano, categoria=args.categoria)
    if not gastos:
        print("Nada encontrado.")
        return

    for g in gastos:
        print(
            f"#{g.id:<4} {g.data.strftime('%d/%m/%Y')}  "
            f"{g.categoria:<12} {formatar_moeda(g.valor):>10}  {g.descricao}"
        )


def cmd_resumo(args: argparse.Namespace) -> None:
    hoje = date.today()
    mes = args.mes or hoje.month
    ano = args.ano or hoje.year
    print(resumo_mensal(mes, ano, args.db))


def cmd_export(args: argparse.Namespace) -> None:
    qtd = exportar_csv(args.arquivo, args.db, mes=args.mes, ano=args.ano)
    print(f"{qtd} registros exportados para {args.arquivo}")


def cmd_rm(args: argparse.Namespace) -> None:
    if remover(args.id, args.db):
        print(f"Gasto #{args.id} removido.")
    else:
        print(f"Gasto #{args.id} não existe.", file=sys.stderr)
        sys.exit(1)


def cmd_categorias(_: argparse.Namespace) -> None:
    print("Categorias sugeridas:")
    for cat in CATEGORIAS_PADRAO:
        print(f"  - {cat}")


def build_parser() -> argparse.ArgumentParser:
    db_parent = _db_parser()

    parser = argparse.ArgumentParser(
        prog="conta-mes",
        description="Anota gastos do dia a dia no terminal.",
    )

    sub = parser.add_subparsers(dest="comando", required=True)

    p_add = sub.add_parser("add", parents=[db_parent], help="registrar um gasto")
    p_add.add_argument("descricao")
    p_add.add_argument("valor", type=_parse_valor)
    p_add.add_argument("-c", "--categoria", default="outros")
    p_add.add_argument("-d", "--data", help="YYYY-MM-DD ou DD/MM/YYYY")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", parents=[db_parent], help="listar gastos")
    p_list.add_argument("-m", "--mes", type=int)
    p_list.add_argument("-a", "--ano", type=int)
    p_list.add_argument("-c", "--categoria")
    p_list.set_defaults(func=cmd_list)

    p_resumo = sub.add_parser("resumo", parents=[db_parent], help="totais por categoria")
    p_resumo.add_argument("-m", "--mes", type=int)
    p_resumo.add_argument("-a", "--ano", type=int)
    p_resumo.set_defaults(func=cmd_resumo)

    p_export = sub.add_parser("export", parents=[db_parent], help="exportar pra CSV")
    p_export.add_argument("arquivo", type=Path)
    p_export.add_argument("-m", "--mes", type=int)
    p_export.add_argument("-a", "--ano", type=int)
    p_export.set_defaults(func=cmd_export)

    p_rm = sub.add_parser("rm", parents=[db_parent], help="apagar um gasto pelo id")
    p_rm.add_argument("id", type=int)
    p_rm.set_defaults(func=cmd_rm)

    p_cat = sub.add_parser("categorias", parents=[db_parent], help="lista categorias sugeridas")
    p_cat.set_defaults(func=cmd_categorias)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as err:
        print(f"Erro: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
