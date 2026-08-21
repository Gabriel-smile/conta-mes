# conta-mes

CLI em Python pra registrar gastos do mês. Eu fiz porque planilha sempre ficava desatualizada e eu queria algo rápido no terminal.

Salva tudo num SQLite local (`~/.conta_mes/gastos.db`). Nada de servidor, login ou coisa complicada.

## O que dá pra fazer

- Registrar gasto com descrição, valor e categoria
- Listar com filtro por mês/ano/categoria
- Ver resumo mensal (% por categoria)
- Exportar CSV
- Apagar registro pelo id

## Requisitos

- Python 3.10+

## Instalação

```bash
git clone https://github.com/Gabriel-smile/conta-mes.git
cd conta-mes
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

Se não quiser instalar como pacote, também roda direto:

```bash
pip install -r requirements.txt
set PYTHONPATH=src   # Windows cmd
# export PYTHONPATH=src   # bash
python -m conta_mes.cli --help
```

## Uso

```bash
# registrar
conta-mes add "mercado" 187.50 -c alimentacao
conta-mes add "uber" 22,90 -c transporte -d 21/08/2025

# listar mês/ano (só -m filtra aquele mês em qualquer ano)
conta-mes list -m 8 -a 2025
conta-mes list -m 8

# banco customizado (--db vai depois do subcomando)
conta-mes list --db ./meu.db

# resumo
conta-mes resumo -m 8 -a 2025

# exportar
conta-mes export gastos_agosto.csv -m 8 -a 2025

# remover
conta-mes rm 3

# categorias sugeridas
conta-mes categorias
```

Categorias que eu costumo usar: `alimentacao`, `transporte`, `moradia`, `lazer`, `saude`, `outros`. Dá pra inventar outras, o programa aceita qualquer texto.

## Testes

```bash
pytest
```

## Estrutura

```
src/conta_mes/
  cli.py       # argparse + comandos
  db.py        # SQLite
  models.py    # dataclass Gasto
  reports.py   # resumo e export CSV
tests/
```

## Próximos passos (se sobrar tempo)

- [ ] meta mensal por categoria
- [ ] importar CSV
- [ ] gráfico simples no terminal

## Licença

MIT
