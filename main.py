"""
main.py
=======
Entry point aplikasi FastAPI dengan Oracle Database.

Konsep yang dipelajari:
- FastAPI Lifespan untuk startup/shutdown
- Inisialisasi Connection Pool
- Router registration
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import create_pool, close_pool, oracle_pool
import app.database as db_module
from app.routers import employees


# ─────────────────────────────────────────────
# LIFESPAN — dijalankan sekali saat startup & shutdown
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager:
    - Kode SEBELUM yield → dijalankan saat startup
    - Kode SETELAH yield → dijalankan saat shutdown

    Ini adalah cara modern FastAPI untuk menggantikan
    @app.on_event("startup") dan @app.on_event("shutdown").
    """
    # ── STARTUP ──
    print("🚀 Aplikasi FastAPI starting up...")
    db_module.oracle_pool = await create_pool()
    print("✅ Oracle connection pool siap digunakan")

    yield  # Aplikasi berjalan di sini

    # ── SHUTDOWN ──
    print("🛑 Aplikasi FastAPI shutting down...")
    await close_pool()


# ─────────────────────────────────────────────
# FASTAPI APP INSTANCE
# ─────────────────────────────────────────────
app = FastAPI(
    title="Chapter 5 — FastAPI + Oracle Database",
    description="""
## Integrasi Oracle Database dengan FastAPI

Aplikasi ini mendemonstrasikan:

- 🔌 **Driver Oracle Python** — menggunakan `oracledb` (resmi dari Oracle)
- 🏊 **Connection Pooling** — efisiensi koneksi dengan shared pool
- 💾 **Transaction** — commit & rollback untuk integritas data
- 🛡️ **Parameter Binding** — mencegah SQL Injection

### Endpoint
CRUD operations untuk resource **Employee** (Karyawan).
    """,
    version="1.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# ROUTER REGISTRATION
# ─────────────────────────────────────────────
app.include_router(employees.router)


# ─────────────────────────────────────────────
# ROOT ENDPOINT — health check
# ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "success": True,
        "message": "Chapter 5 — FastAPI + Oracle Database",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Cek status koneksi Oracle."""
    pool = db_module.oracle_pool
    if pool is None:
        return {"success": False, "message": "Pool belum diinisialisasi"}

    return {
        "success": True,
        "message": "Koneksi Oracle OK",
        "pool": {
            "min": pool.min,
            "max": pool.max,
            "increment": pool.increment,
            "timeout": pool.timeout,
        },
    }
