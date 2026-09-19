import secrets
import string
import sqlite3
import os
import random
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "apex_market.db")


def generate_token(length=28) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance INTEGER DEFAULT 0,
                registered_at TEXT DEFAULT (datetime('now')),
                status TEXT DEFAULT 'Активен'
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id TEXT,
                product_name TEXT,
                price INTEGER,
                payment_method TEXT,
                status TEXT DEFAULT 'pending',
                token TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                confirmed_at TEXT
            );
        """)
        try:
            db.execute("ALTER TABLE orders ADD COLUMN token TEXT")
        except:
            pass
        try:
            db.execute("ALTER TABLE orders ADD COLUMN qty INTEGER DEFAULT 1")
        except:
            pass

        db.executescript("""
            CREATE TABLE IF NOT EXISTS token_meta (
                token TEXT PRIMARY KEY,
                quality TEXT NOT NULL,
                quality_pct INTEGER NOT NULL,
                buyback_price INTEGER NOT NULL,
                needs_proxy INTEGER DEFAULT 0,
                proxy_type TEXT DEFAULT '',
                needs_cert INTEGER DEFAULT 0,
                cert_type TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS promocodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                discount_percent INTEGER NOT NULL,
                max_activations INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)


def register_user(user_id: int, username: str | None, first_name: str | None):
    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name),
        )


def get_all_users() -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT user_id, username, first_name, balance, status, registered_at FROM users ORDER BY balance DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_balance(user_id: int, amount: int) -> int:
    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,),
        )
        db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id),
        )
        row = db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row["balance"] if row else 0


def get_user(user_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_orders(user_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_order_stats(user_id: int) -> tuple[int, int]:
    with get_db() as db:
        row = db.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(price), 0) as total FROM orders WHERE user_id = ? AND status = 'confirmed'",
            (user_id,),
        ).fetchone()
        return (row["cnt"], row["total"])


def create_order(user_id: int, product_id: str, product_name: str, price: int, payment_method: str, qty: int = 1) -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO orders (user_id, product_id, product_name, price, payment_method, qty) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, product_id, product_name, price, payment_method, qty),
        )
        return cur.lastrowid


def get_pending_orders() -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def confirm_order(order_id: int) -> bool:
    with get_db() as db:
        db.execute(
            "UPDATE orders SET status = 'confirmed', confirmed_at = datetime('now') WHERE id = ?",
            (order_id,),
        )
        row = db.execute("SELECT id FROM orders WHERE id = ? AND user_id IS NOT NULL", (order_id,)).fetchone()
    return row is not None


def claim_order(order_id: int) -> list[dict] | None:
    with get_db() as db:
        row = db.execute("SELECT qty, token FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return None
        if row["token"]:
            return None
        qty = row["qty"] or 1
        tokens = [generate_token() for _ in range(qty)]
        tokens_str = ",".join(tokens)
        db.execute(
            "UPDATE orders SET token = ? WHERE id = ?",
            (tokens_str, order_id),
        )
        metas = []
        for t in tokens:
            quality_emoji, quality_pct = random.choice(QUALITIES)
            buyback_price = random.randint(12000, 15000)
            case = random.choice(["none", "proxy", "cert", "both"])
            needs_proxy = 1 if case in ("proxy", "both") else 0
            needs_cert = 1 if case in ("cert", "both") else 0
            proxy_type = random.choice(PROXY_TYPES) if needs_proxy else ""
            cert_type = random.choice(CERT_TYPES) if needs_cert else ""
            db.execute(
                "INSERT OR REPLACE INTO token_meta (token, quality, quality_pct, buyback_price, needs_proxy, proxy_type, needs_cert, cert_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (t, quality_emoji, quality_pct, buyback_price, needs_proxy, proxy_type, needs_cert, cert_type),
            )
            metas.append({
                "token": t,
                "quality": quality_emoji,
                "quality_pct": quality_pct,
                "buyback_price": buyback_price,
                "needs_proxy": needs_proxy,
                "proxy_type": proxy_type,
                "needs_cert": needs_cert,
                "cert_type": cert_type,
            })
    return metas


def get_order(order_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return dict(row) if row else None


def get_order_user_id(order_id: int) -> int | None:
    with get_db() as db:
        row = db.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,)).fetchone()
        return row["user_id"] if row else None


def reject_order(order_id: int):
    with get_db() as db:
        db.execute(
            "UPDATE orders SET status = 'rejected' WHERE id = ?",
            (order_id,),
        )


def create_promocode(code: str, discount_percent: int, max_activations: int):
    with get_db() as db:
        db.execute(
            "INSERT INTO promocodes (code, discount_percent, max_activations) VALUES (?, ?, ?)",
            (code.upper(), discount_percent, max_activations),
        )


def get_promocode(code: str) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM promocodes WHERE code = ?", (code.upper(),)
        ).fetchone()
        return dict(row) if row else None


def use_promocode(code: str) -> bool:
    with get_db() as db:
        row = db.execute(
            "SELECT id, max_activations, used_count FROM promocodes WHERE code = ?",
            (code.upper(),),
        ).fetchone()
        if not row:
            return False
        if row["used_count"] >= row["max_activations"]:
            return False
        db.execute(
            "UPDATE promocodes SET used_count = used_count + 1 WHERE id = ?",
            (row["id"],),
        )
        return True


def list_promocodes() -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM promocodes ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def delete_promocode(code: str):
    with get_db() as db:
        db.execute("DELETE FROM promocodes WHERE code = ?", (code.upper(),))


QUALITIES = [
    ("📀 Низкое", 45),
    ("💿 Среднее", 65),
    ("✨ Хорошее", 80),
    ("🔥 Отличное", 95),
    ("💎 Премиум", 100),
]

PROXY_TYPES = ["IPv4", "IPv6", "Mobile"]
CERT_TYPES = ["Clean", "Express", "GUARANTEE"]


def generate_token_meta(token: str) -> dict:
    quality_emoji, quality_pct = random.choice(QUALITIES)
    buyback_price = random.randint(12000, 15000)
    case = random.choice(["none", "proxy", "cert", "both"])
    needs_proxy = 1 if case in ("proxy", "both") else 0
    needs_cert = 1 if case in ("cert", "both") else 0
    proxy_type = random.choice(PROXY_TYPES) if needs_proxy else ""
    cert_type = random.choice(CERT_TYPES) if needs_cert else ""

    meta = {
        "token": token,
        "quality": quality_emoji,
        "quality_pct": quality_pct,
        "buyback_price": buyback_price,
        "needs_proxy": needs_proxy,
        "proxy_type": proxy_type,
        "needs_cert": needs_cert,
        "cert_type": cert_type,
    }
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO token_meta (token, quality, quality_pct, buyback_price, needs_proxy, proxy_type, needs_cert, cert_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (token, quality_emoji, quality_pct, buyback_price, needs_proxy, proxy_type, needs_cert, cert_type),
        )
    return meta


def get_token_meta(token: str) -> dict | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM token_meta WHERE token = ?", (token,)).fetchone()
        return dict(row) if row else None


def apply_converter(token: str) -> dict | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM token_meta WHERE token = ?", (token,)).fetchone()
        if not row:
            return None
        if row["quality_pct"] == 100:
            return {"already_premium": True}
        db.execute(
            "UPDATE token_meta SET quality = '💎 Премиум', quality_pct = 100, "
            "buyback_price = buyback_price + 5000, "
            "needs_proxy = 0, proxy_type = '', "
            "needs_cert = 0, cert_type = '' "
            "WHERE token = ?",
            (token,),
        )
        row = db.execute("SELECT * FROM token_meta WHERE token = ?", (token,)).fetchone()
        return dict(row)
