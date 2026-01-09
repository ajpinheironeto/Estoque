from datetime import datetime
from typing import Optional
import io

from nicegui import ui
from fastapi import UploadFile, File
from models import ProductCreate, Product
import database

# initialize db
database.init_db()

# pagination/search state
PAGE_SIZES = [5, 10, 20]
page = 1
page_size = PAGE_SIZES[0]
search_name = ''
search_sku = ''
sort_by = 'id'
sort_desc = True

editing_id: Optional[int] = None

# inline edit flags
_inline_edit_flags = set()

# UI elements placeholders
name_search = sku_search = sort_select = order_toggle = None
input_name = input_sku = input_price = input_quantity = input_category = input_description = None
save_button = current_delete_button = cancel_button = None
product_list_container = None
page_label = None
page_size_select = None


def refresh_list(container):
    container.clear()
    total = database.count_products(name=search_name or None, sku=search_sku or None)
    offset = (page - 1) * page_size
    products = database.list_products(name=search_name or None, sku=search_sku or None, sort_by=sort_by, desc=sort_desc, limit=page_size, offset=offset)

    if not products:
        ui.label('Nenhum produto encontrado.').style('margin-top: 8px;').bind(container)
        return

    for p in products:
        inline = p.id in _inline_edit_flags
        with container.card().style('margin-bottom: 8px;'):
            with ui.row().style('justify-content: space-between; align-items: center;'):
                if inline:
                    # inline inputs
                    name_i = ui.input(value=p.name, placeholder='Nome')
                    sku_i = ui.input(value=p.sku or '', placeholder='SKU')
                    price_i = ui.input(value=p.price, type='number')
                    qty_i = ui.input(value=p.quantity, type='number')
                    cat_i = ui.input(value=p.category or '')
                    desc_i = ui.input(value=p.description or '')
                    with ui.row():
                        ui.button('Salvar', on_click=lambda e, pid=p.id, ni=name_i, si=sku_i, pr=price_i, qu=qty_i, ca=cat_i, de=desc_i: save_inline(pid, ni, si, pr, qu, ca, de))
                        ui.button('Cancelar', on_click=lambda e, pid=p.id: cancel_inline(pid)).props('flat')
                else:
                    with ui.column():
                        ui.markdown(f'**{p.name}**  \nSKU: `{p.sku or "-"}`  \nPreço: R$ {p.price:.2f}  \nQtd: {p.quantity}  \nCategoria: {p.category or "-"}')
                    with ui.row():
                        ui.button('Editar', on_click=lambda e, prod=p: start_edit(prod)).props('flat').style('margin-right: 8px;')
                        ui.button('Editar inline', on_click=lambda e, prod=p: start_inline_edit(prod)).props('flat').style('margin-right: 8px;')
                        ui.button('Excluir', on_click=lambda e, pid=p.id: delete_product(pid)).props('flat').style('color: red;')

    # update page label
    if page_label:
        page_label.set_text(f'Página {page} — {total} itens')


# inline edit functions

def start_inline_edit(prod: Product):
    _inline_edit_flags.add(prod.id)
    refresh_list(product_list_container)


def save_inline(pid, ni, si, pr, qu, ca, de):
    try:
        payload = ProductCreate(
            name=ni.value or '',
            sku=si.value or None,
            price=float(pr.value or 0),
            quantity=int(qu.value or 0),
            category=ca.value or None,
            description=de.value or None,
        )
        updated = database.update_product(pid, payload)
        ui.notify('Atualizado' if updated else 'Não encontrado', color='positive' if updated else 'warning')
    except Exception as e:
        ui.notify(f'Erro: {e}', color='negative')
    finally:
        _inline_edit_flags.discard(pid)
        refresh_list(product_list_container)


def cancel_inline(pid):
    _inline_edit_flags.discard(pid)
    refresh_list(product_list_container)


# form edit functions (existing form on the left)

def start_edit(product: Product):
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


# CSV export / import handlers

def export_csv_handler():
    data = database.export_csv(name=search_name or None, sku=search_sku or None)
    return ('estoque.csv', data)


async def import_csv_handler(file: UploadFile = File(...), update_existing: bool = False):
    content = await file.read()
    added, updated = database.import_csv_bytes(content, update_existing=update_existing)
    return {"added": added, "updated": updated}


# REST API (attach to underlying FastAPI app)
fastapi_app = ui.get_app()


@fastapi_app.get('/api/products')
async def api_list_products(name: Optional[str] = None, sku: Optional[str] = None, page_param: int = 1, page_size_param: int = 10):
    total = database.count_products(name=name, sku=sku)
    offset = (page_param - 1) * page_size_param
    items = database.list_products(name=name, sku=sku, limit=page_size_param, offset=offset)
    return {"total": total, "items": [p.dict() for p in items]}


@fastapi_app.post('/api/products')
async def api_create_product(payload: ProductCreate):
    pid = database.add_product(payload)
    return {"id": pid}


@fastapi_app.get('/api/products/{product_id}')
async def api_get_product(product_id: int):
    p = database.get_product(product_id)
    if not p:
        return {"error": "not found"}
    return p.dict()


@fastapi_app.put('/api/products/{product_id}')
async def api_update_product(product_id: int, payload: ProductCreate):
    ok = database.update_product(product_id, payload)
    return {"updated": ok}


@fastapi_app.delete('/api/products/{product_id}')
async def api_delete_product(product_id: int):
    ok = database.delete_product(product_id)
    return {"deleted": ok}


# UI layout
with ui.column().style('max-width: 1000px; margin: 20px;'):
    ui.label('Estoque - Cadastro de Produtos').style('font-weight:700; font-size:22px;')
    with ui.row().style('gap: 8px; align-items:center;'):
        name_search = ui.input('Buscar por nome', on_change=lambda e: on_search_change()).style('width: 240px;')
        sku_search = ui.input('Buscar por SKU', on_change=lambda e: on_search_change()).style('width: 180px;')
        sort_select = ui.select(['id', 'name', 'price', 'quantity'], value='id', on_change=lambda e: on_sort_change()).style('width: 140px;')
        order_toggle = ui.checkbox('Decrescente', value=True, on_change=lambda e: on_sort_change())
        ui.button('Exportar CSV', on_click=lambda e: ui.download(export_csv_handler())).style('margin-left: 16px;')
        ui.file_upload(on_upload=lambda files: on_upload_files(files)).props('accept=.csv')

    with ui.row().style('gap: 40px; align-items:flex-start; margin-top: 12px;'):
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
            # page controls
            with ui.row().style('gap: 8px; align-items:center;'):
                ui.button('<<', on_click=lambda e: goto_page(1))
                ui.button('<', on_click=lambda e: goto_prev())
                page_label = ui.label('Página 1')
                ui.button('>', on_click=lambda e: goto_next())
                ui.button('>>', on_click=lambda e: goto_last())
                page_size_select = ui.select(PAGE_SIZES, value=PAGE_SIZES[0], on_change=lambda e: on_page_size_change()).style('width: 100px;')

            product_list_container = ui.column()
            refresh_list(product_list_container)


# helpers for search / pagination

def on_search_change():
    global page, search_name, search_sku
    page = 1
    search_name = name_search.value or ''
    search_sku = sku_search.value or ''
    refresh_list(product_list_container)


def on_sort_change():
    global sort_by, sort_desc
    sort_by = sort_select.value or 'id'
    sort_desc = order_toggle.value
    refresh_list(product_list_container)


def goto_page(n: int):
    global page
    page = max(1, n)
    refresh_list(product_list_container)


def goto_prev():
    global page
    if page > 1:
        page -= 1
        refresh_list(product_list_container)


def goto_next():
    global page
    total = database.count_products(name=search_name or None, sku=search_sku or None)
    last = (total - 1) // page_size + 1
    if page < last:
        page += 1
        refresh_list(product_list_container)


def goto_last():
    global page
    total = database.count_products(name=search_name or None, sku=search_sku or None)
    page = (total - 1) // page_size + 1 if total > 0 else 1
    refresh_list(product_list_container)


def on_page_size_change():
    global page_size, page
    page_size = int(page_size_select.value)
    page = 1
    refresh_list(product_list_container)


# file upload handler for CSVs

def on_upload_files(files):
    for f in files:
        data = f.content if hasattr(f, 'content') else f['content']
        added, updated = database.import_csv_bytes(data, update_existing=True)
        ui.notify(f'Importado: {added} adicionados, {updated} atualizados', color='positive')
    refresh_list(product_list_container)


ui.open()
ui.run(title='Estoque - Cadastro de Produtos', reload=False)
