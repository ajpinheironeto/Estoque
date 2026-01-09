Estoque - Cadastro de Produtos

This is a small inventory (estoque) web app using NiceGUI + FastAPI and a SQLite database.

Quick start

1. Install dependencies:

   pip install -r requirements.txt

2. Run the app:

   python app.py

   The NiceGUI interface will open (by default at http://localhost:8080).

API

The underlying FastAPI app exposes a simple REST API under /api:

- GET /api/products
  - Query params: name (optional), sku (optional), page_param (int), page_size_param (int)
  - Returns: { total: int, items: [product] }

- POST /api/products
  - Body: ProductCreate JSON
  - Returns: { id: new_product_id }

- GET /api/products/{product_id}
  - Returns product JSON or { error: "not found" }

- PUT /api/products/{product_id}
  - Body: ProductCreate JSON
  - Returns: { updated: true/false }

- DELETE /api/products/{product_id}
  - Returns: { deleted: true/false }

Example (list products):

  curl "http://localhost:8080/api/products?page_param=1&page_size_param=10"

CSV import / export

- Export: use the "Exportar CSV" button in the UI — this will download a CSV with headers:
  id,name,sku,price,quantity,description,category,created_at

- Import: use the file upload control in the UI (accepts .csv). Uploaded rows are parsed and added. When uploading via the UI, existing products with matching SKU are updated.

CSV format notes:
- Required columns for import: name, price, quantity
- Optional columns: sku, description, category
- price should be a number (dot decimal); quantity should be an integer

Database

The app uses a local SQLite file named estoque.db by default (DB_PATH in database.py).

Models

See models.py for Pydantic model definitions used by the app.

If you need other changes, tell me which files to modify or confirm any additional requirements.