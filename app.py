from datetime import datetime
from typing import Optional

from nicegui import ui
from models import ProductCreate
import database

database.init_db()

editing_id: Optional[int] = None

# UI elements (will be created below)
input_name = input_sku = input_price = input_quantity = input_category = input_description = None
save_button = None
cancel_button = None
current_delete_button = None
product_list_container = None


def refresh_list(container):
    container.clear()
    products = database.list_products()

    if not products:
        ui.label('Nenhum produto cadastrado.').style('margin-top: 8px;').bind(container)
        return

    for p in products:
        with container.card().style('margin-bottom: 8px;'):
            with ui.row().style('justify-content: space-between; align-items: center;'):
                with ui.column():
                    ui.markdown(f'**{p.name}**  \nSKU: `{p.sku or "-"}  `\nPreço: R$ {p.price:.2f}  \nQtd: {p.quantity}  \nCategoria: {p.category or "-"}')
                with ui.row():
                    ui.button('Editar', on_click=lambda e, prod=p: start_edit(prod)).props('flat').style('margin-right: 8px;')
                    ui.button('Excluir', on_click=lambda e, pid=p.id: delete_product(pid)).props('flat').style('color: red;')


def start_edit(product):
    global editing_id
    editing_id = product.id
    input_name.value = product.name
    input_sku.value = product.sku or ''
    input_price.value = product.price
    input_quantity.value = product.quantity
    input_category.value = product.category or ''
    input_description.value = product.description or ''
    save_button.set_text('Salvar alterações')
    current_delete_button.style('display: inline-block;')


def clear_form():
    global editing_id
    editing_id = None
    input_name.value = ''
    input_sku.value = ''
    input_price.value = 0.0
    input_quantity.value = 0
    input_category.value = ''
    input_description.value = ''
    save_button.set_text('Salvar produto')
    current_delete_button.style('display: none;')


def on_submit():
    global editing_id
    payload = {
        'name': input_name.value or '',
        'sku': input_sku.value or None,
        'price': float(input_price.value or 0),
        'quantity': int(input_quantity.value or 0),
        'category': input_category.value or None,
        'description': input_description.value or None,
    }
    try:
        product = ProductCreate(**payload)
    except Exception as e:
        ui.notify(f'Erro de validação: {e}', color='negative')
        return

    try:
        if editing_id is None:
            database.add_product(product)
            ui.notify('Produto cadastrado com sucesso.', color='positive')
        else:
            updated = database.update_product(editing_id, product)
            if updated:
                ui.notify('Produto atualizado com sucesso.', color='positive')
            else:
                ui.notify('Produto não encontrado para atualização.', color='warning')
        clear_form()
        refresh_list(product_list_container)
    except Exception as e:
        ui.notify(f'Erro ao salvar: {e}', color='negative')


def delete_product(product_id: int):
    def do_delete():
        try:
            deleted = database.delete_product(product_id)
            if deleted:
                ui.notify('Produto excluído.', color='positive')
            else:
                ui.notify('Produto não encontrado.', color='warning')
            clear_form()
            refresh_list(product_list_container)
        except Exception as e:
            ui.notify(f'Erro ao excluir: {e}', color='negative')

    ui.confirm('Confirma exclusão do produto?', on_confirm=do_delete)


with ui.row().style('gap: 40px; align-items:flex-start;'):
    with ui.column().style('width: 420px;'):
        ui.label('Cadastro de Produto').style('font-weight:700; font-size:18px;')
        input_name = ui.input('Nome', placeholder='Nome do produto')
        input_sku = ui.input('SKU (opcional)', placeholder='Código/SKU')
        input_price = ui.input('Preço', type='number', value=0.0)
        input_quantity = ui.input('Quantidade', type='number', value=0)
        input_category = ui.input('Categoria (opcional)')
        input_description = ui.textarea('Descrição (opcional)')

        with ui.row().style('gap: 8px; margin-top: 8px'):
            save_button = ui.button('Salvar produto', on_click=on_submit)
            current_delete_button = ui.button('Excluir produto atual', on_click=lambda e: delete_product(editing_id)).style('display: none;').props('flat')
            cancel_button = ui.button('Cancelar', on_click=lambda e: clear_form()).props('flat')

    with ui.column():
        ui.label('Estoque').style('font-weight:700; font-size:18px;')
        product_list_container = ui.column()
        refresh_list(product_list_container)


ui.open()
ui.run(title='Estoque - Cadastro de Produtos', reload=False)
