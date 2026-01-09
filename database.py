import sqlite3
from datetime import datetime
from typing import List, Optional

from models import Product, ProductCreate

DB_PATH = "estoque.db"


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


def list_products() -> List[Product]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    products = []
    for r in rows:
        products.append(
            Product(
                id=r["id"],
                name=r["name"],
                sku=r["sku"],
                price=r["price"],
                quantity=r["quantity"],
                description=r["description"],
                category=r["category"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
        )
    return products


def get_product(product_id: int) -> Optional[Product]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return Product(
        id=r["id"],
        name=r["name"],
        sku=r["sku"],
        price=r["price"],
        quantity=r["quantity"],
        description=r["description"],
        category=r["category"],
        created_at=datetime.fromisoformat(r["created_at"]),
    )
