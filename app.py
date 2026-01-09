from datetime import datetime
from typing import List

from nicegui import ui
from models import ProductCreate
import database


database.init_db()


def refresh_table(table):
    products = database.list_products()
    table.rows = [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku or "",
            "price": f"{p.price:.2f}",
            "quantity": p.quantity,
            "category": p.category or "",
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for p in products
    ]


with ui.row().style("gap: 40px; align-items:flex-start;"):
    with ui.column().style("width: 420px;"):
        ui.label("Cadastro de Produto").style("font-weight:700; font-size:18px;")
        input_name = ui.input("Nome", placeholder="Nome do produto")
        input_sku = ui.input("SKU (opcional)", placeholder="Código/SKU")
        input_price = ui.input("Preço", type="number", value=0.0)
        input_quantity = ui.input("Quantidade", type="number", value=0)
        input_category = ui.input("Categoria (opcional)")
        input_description = ui.textarea("Descrição (opcional)")

        msg = ui.label("")

        def on_submit():
            payload = {
                "name": input_name.value or "",
                "sku": input_sku.value or None,
                "price": float(input_price.value or 0),
                "quantity": int(input_quantity.value or 0),
                "category": input_category.value or None,
                "description": input_description.value or None,
            }
            try:
                product = ProductCreate(**payload)
            except Exception as e:
                msg.set_text(f"Erro de validação: {e}")
                msg.style("color: red;")
                return
            try:
                database.add_product(product)
                msg.set_text("Produto cadastrado com sucesso.")
                msg.style("color: green;")
                # limpa campos
                input_name.value = ""
                input_sku.value = ""
                input_price.value = 0.0
                input_quantity.value = 0
                input_category.value = ""
                input_description.value = ""
                # atualizar tabela
                refresh_table(product_table)
            except Exception as e:
                msg.set_text(f"Erro ao salvar: {e}")
                msg.style("color: red;")

        ui.button("Salvar produto", on_click=on_submit).style("margin-top: 8px;")

    with ui.column():
        ui.label("Estoque").style("font-weight:700; font-size:18px;")
        product_table = ui.table(
            columns=[
                {"name": "id", "label": "ID"},
                {"name": "name", "label": "Nome"},
                {"name": "sku", "label": "SKU"},
                {"name": "price", "label": "Preço"},
                {"name": "quantity", "label": "Qtd"},
                {"name": "category", "label": "Categoria"},
                {"name": "created_at", "label": "Criado em"},
            ],
            rows=[],
            height="60vh",
        )
        refresh_table(product_table)


ui.open()
ui.run(title="Estoque - Cadastro de Produtos", reload=False)
