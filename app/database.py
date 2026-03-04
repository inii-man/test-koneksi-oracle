"""
app/database.py
===============
Modul koneksi Oracle Database menggunakan library oracledb (python-oracledb).

Konsep yang dipelajari:
- Driver Oracle Python (oracledb)
- Connection Pooling (oracledb.create_pool_async)
- Dependency Injection ke FastAPI
"""

import oracledb
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ─────────────────────────────────────────────
# 1. SETTINGS — membaca konfigurasi dari .env
# ─────────────────────────────────────────────
class OracleSettings(BaseSettings):
    """
    Membaca variabel dari file .env secara otomatis.
    pydantic-settings memetakan nama variabel env ke field class ini.
    """
    oracle_user: str
    oracle_password: str
    oracle_host: str = "localhost"
    oracle_port: int = 1521
    oracle_service: str = "freepdb1"

    # Pool settings
    oracle_pool_min: int = 2
    oracle_pool_max: int = 10
    oracle_pool_increment: int = 1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def dsn(self) -> str:
        """
        DSN = Data Source Name — string identifikasi koneksi Oracle.
        Format: host:port/service_name
        Contoh: localhost:1521/freepdb1
        """
        return f"{self.oracle_host}:{self.oracle_port}/{self.oracle_service}"


# Instance singleton untuk seluruh aplikasi
settings = OracleSettings()


# ─────────────────────────────────────────────
# 2. CONNECTION POOL — dikelola satu kali di startup
# ─────────────────────────────────────────────

# Variabel global untuk menyimpan pool (diinisialisasi saat startup FastAPI)
oracle_pool: oracledb.AsyncConnectionPool | None = None


async def create_pool() -> oracledb.AsyncConnectionPool:
    """
    Membuat connection pool Oracle secara async.

    Connection Pool adalah sekumpulan koneksi yang dibuat di awal
    dan dipakai bersama-sama oleh semua request. Ini jauh lebih
    efisien daripada membuat koneksi baru di setiap request.

    Parameter:
    - min: jumlah koneksi minimum yang selalu aktif
    - max: jumlah koneksi maksimum yang boleh dibuat
    - increment: jumlah koneksi baru yang dibuat ketika pool habis
    """
    print(f"[DB] Membuat connection pool ke Oracle DSN: {settings.dsn}")
    print(f"[DB] User: {settings.oracle_user}")
    print(f"[DB] Pool min={settings.oracle_pool_min}, max={settings.oracle_pool_max}")

    pool = oracledb.create_pool_async(
        user=settings.oracle_user,
        password=settings.oracle_password,
        dsn=settings.dsn,
        min=settings.oracle_pool_min,
        max=settings.oracle_pool_max,
        increment=settings.oracle_pool_increment,
    )
    print("[DB] ✅ Connection pool berhasil dibuat!")
    return pool


async def close_pool() -> None:
    """Menutup semua koneksi dalam pool saat aplikasi shutdown."""
    global oracle_pool
    if oracle_pool:
        await oracle_pool.close()
        print("[DB] 🔌 Connection pool ditutup.")


# ─────────────────────────────────────────────
# 3. DEPENDENCY INJECTION — get_cursor()
# ─────────────────────────────────────────────

@asynccontextmanager
async def get_cursor() -> AsyncGenerator[oracledb.AsyncCursor, None]:
    """
    Async context manager untuk mendapatkan cursor dari pool.

    Context manager ini:
    1. Mengambil satu koneksi dari pool
    2. Membuat cursor untuk eksekusi SQL
    3. Yield cursor ke endpoint
    4. Menutup cursor dan mengembalikan koneksi ke pool

    Digunakan sebagai FastAPI Dependency:
        async with get_cursor() as cursor:
            await cursor.execute(...)
    """
    global oracle_pool
    if oracle_pool is None:
        raise RuntimeError("Connection pool belum diinisialisasi!")

    # Ambil koneksi dari pool
    async with oracle_pool.acquire() as connection:
        # Buat cursor untuk menjalankan SQL
        async with connection.cursor() as cursor:
            yield cursor, connection


async def get_db():
    """
    FastAPI Dependency untuk mendapatkan (cursor, connection).

    Penggunaan di endpoint:
        @router.get("/")
        async def list_data(db=Depends(get_db)):
            cursor, conn = db
    """
    global oracle_pool
    if oracle_pool is None:
        raise RuntimeError("Connection pool belum diinisialisasi!")

    async with oracle_pool.acquire() as connection:
        async with connection.cursor() as cursor:
            yield cursor, connection
