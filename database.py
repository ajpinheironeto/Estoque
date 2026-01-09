import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple
import csv
import io

from models import Product, ProductCreate

DB_PATH = "estoque.db"

ALLOWED_SORT_COLUMNS = {"id", "name", "price", "quantity", "created_at"}


def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            description TEXT,
            category TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_product(data: ProductCreate) -> int:
    conn = get_conn()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO products (name, sku, price, quantity, description, category, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (data.name, data.sku, data.price, data.quantity, data.description, data.category, created_at),
    )
    conn.commit()
    product_id = cur.lastrowid
    conn.close()
    return product_id


def update_product(product_id: int, data: ProductCreate) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE products
        SET name = ?, sku = ?, price = ?, quantity = ?, description = ?, category = ?
        WHERE id = ?
        """,
        (data.name, data.sku, data.price, data.quantity, data.description, data.category, product_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


def delete_product(product_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def _build_filters_query(name: Optional[str], sku: Optional[str]) -> Tuple[str, List[object]]:
    clauses: List[str] = []
    params: List[object] = []
    if name:
        clauses.append("name LIKE ?")
        params.append(f"%{name}%")
    if sku:
        clauses.append("sku LIKE ?")
        params.append(f"%{sku}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def list_products(name: Optional[str] = None, sku: Optional[str] = None, sort_by: str = 'id', desc: bool = True, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Product]:
    conn = get_conn()
    cur = conn.cursor()
    where, params = _build_filters_query(name, sku)
    # validate sort_by
    if sort_by not in ALLOWED_SORT_COLUMNS:
        sort_by = 'id'
    order = f"ORDER BY {sort_by} {'DESC' if desc else 'ASC'}"
    limit_offset_clause = ''
    if limit is not None:
        limit_offset_clause = 'LIMIT ?'
        params.append(limit)
        if offset is not None:
            limit_offset_clause += ' OFFSET ?'
            params.append(offset)
    query = f"SELECT * FROM products {where} {order} {limit_offset_clause}"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    products: List[Product] = []
    for r in rows:
        products.append(
            Product(
                id=r['id'],
                name=r['name'],
                sku=r['sku'],
                price=r['price'],
                quantity=r['quantity'],
                description=r['description'],
                category=r['category'],
                created_at=datetime.fromisoformat(r['created_at']),
            )
        )
    return products


def count_products(name: Optional[str] = None, sku: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    where, params = _build_filters_query(name, sku)
    query = f"SELECT COUNT(*) as cnt FROM products {where}"
    cur.execute(query, params)
    r = cur.fetchone()
    conn.close()
    return r['cnt'] if r else 0


def export_csv(name: Optional[str] = None, sku: Optional[str] = None) -> bytes:
    products = list_products(name=name, sku=sku, sort_by='id', desc=False)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "sku", "price", "quantity", "description", "category", "created_at"])
    for p in products:
        writer.writerow([p.id, p.name, p.sku or "", f"{p.price:.2f}", p.quantity, p.description or "", p.category or "", p.created_at.isoformat()])
    return output.getvalue().encode('utf-8')


def import_csv_bytes(data: bytes, update_existing: bool = False) -> Tuple[int, int]:
    text = data.decode('utf-8')
    reader = csv.DictReader(io.StringIO(text))
    added = 0
    updated = 0
    for row in reader:
        try:
            payload = ProductCreate(
                name=(row.get('name') or '').strip(),
                sku=(row.get('sku') or '').strip() or None,
                price=float(row.get('price') or 0),
                quantity=int(float(row.get('quantity') or 0)),
                description=(row.get('description') or '').strip() or None,
                category=(row.get('category') or '').strip() or None,
            )
        except Exception:
            continue
        if payload.sku and update_existing:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute('SELECT id FROM products WHERE sku = ?', (payload.sku,))
            r = cur.fetchone()
            conn.close()
            if r:
                update_product(r['id'], payload)
                updated += 1
                continue
        add_product(payload)
        added += 1
    return added, updated


def get_product(product_id: int) -> Optional[Product]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return Product(
        id=r['id'],
        name=r['name'],
        sku=r['sku'],
        price=r['price'],
        quantity=r['quantity'],
        description=r['description'],
        category=r['category'],
        created_at=datetime.fromisoformat(r['created_at']),
    )
