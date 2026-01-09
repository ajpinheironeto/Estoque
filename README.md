```markdown
# Estoque - Cadastro de Produtos (NiceGUI + Pydantic + SQLite)

Requisitos:
- Python 3.10+

Instalação:
```bash
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
```

Rodando:
```bash
python app.py
```

A interface ficará disponível em http://localhost:8080

Arquivos:
- app.py        -> aplicação NiceGUI (formulário + tabela)
- models.py     -> modelos Pydantic (ProductCreate / Product)
- database.py   -> acesso SQLite e operações básicas
- requirements.txt

Observações:
- O banco SQLite será criado no arquivo `estoque.db`.
- Se quiser, posso adicionar funcionalidades adicionais: edição, exclusão, filtros, busca por SKU, export CSV, autenticação, testes, etc.
```
