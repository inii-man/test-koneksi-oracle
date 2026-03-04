"""
demo/demo_connection.py
=======================
Demo: Cara koneksi ke Oracle Database menggunakan oracledb.

Jalankan dengan:
    python demo/demo_connection.py
"""

import asyncio
import oracledb
from dotenv import load_dotenv
import os

# Load konfigurasi dari .env
load_dotenv()

ORACLE_USER     = os.getenv("ORACLE_USER", "system")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "oracle")
ORACLE_HOST     = os.getenv("ORACLE_HOST", "localhost")
ORACLE_PORT     = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_SERVICE  = os.getenv("ORACLE_SERVICE", "freepdb1")
DSN = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"


async def demo_basic_connection():
    """
    Demo 1: Koneksi langsung (single connection)
    Ini cara paling sederhana tapi TIDAK efisien untuk production.
    """
    print("\n" + "="*60)
    print("DEMO 1: Koneksi Langsung (Single Connection)")
    print("="*60)

    # oracledb.connect_async membuat SATU koneksi baru
    conn = await oracledb.connect_async(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN,
    )
    print(f"✅ Koneksi berhasil!")
    print(f"   User     : {conn.username}")
    print(f"   DSN      : {DSN}")
    print(f"   Version  : {conn.version}")

    # Jalankan query sederhana
    cursor = conn.cursor()
    await cursor.execute("SELECT SYSDATE FROM dual")
    row = await cursor.fetchone()
    print(f"   SYSDATE  : {row[0]}")

    cursor.close()
    await conn.close()
    print("🔌 Koneksi ditutup")


async def demo_connection_pool():
    """
    Demo 2: Connection Pool
    Pool lebih efisien karena koneksi dibuat sekali dan dipakai bersama.
    """
    print("\n" + "="*60)
    print("DEMO 2: Connection Pool")
    print("="*60)

    # Buat pool dengan min=2, max=5 koneksi
    pool = await oracledb.create_pool_async(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN,
        min=2,
        max=5,
        increment=1,
    )
    print(f"✅ Pool dibuat!")
    print(f"   Min koneksi   : {pool.min}")
    print(f"   Max koneksi   : {pool.max}")
    print(f"   Koneksi aktif : {pool.opened}")
    print(f"   Koneksi bebas : {pool.free}")

    # Ambil koneksi dari pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT 'Halo dari Oracle!' AS pesan FROM dual"
            )
            row = await cursor.fetchone()
            print(f"\n   Query result : {row[0]}")
            print(f"   Busy saat query : {pool.busy}")

    # Setelah blok selesai, koneksi dikembalikan ke pool
    print(f"   Busy setelah selesai : {pool.busy}")
    print(f"   Free setelah selesai : {pool.free}")

    await pool.close()
    print("🔌 Pool ditutup")


async def demo_query_oracle_version():
    """
    Demo 3: Query informasi Oracle Database
    """
    print("\n" + "="*60)
    print("DEMO 3: Informasi Oracle Database")
    print("="*60)

    conn = await oracledb.connect_async(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN,
    )
    cursor = conn.cursor()

    queries = {
        "Versi Oracle": "SELECT * FROM v$version WHERE rownum = 1",
        "User saat ini": "SELECT USER FROM dual",
        "Waktu server": "SELECT TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') FROM dual",
        "NLS Charset": "SELECT VALUE FROM nls_session_parameters WHERE PARAMETER = 'NLS_CHARACTERSET'",
    }

    for label, sql in queries.items():
        try:
            await cursor.execute(sql)
            row = await cursor.fetchone()
            print(f"   {label:20}: {row[0]}")
        except Exception as e:
            print(f"   {label:20}: (tidak dapat diakses) {e}")

    cursor.close()
    await conn.close()


async def main():
    print("\n🔬 DEMO KONEKSI ORACLE DATABASE")
    print("Library: python-oracledb (driver resmi Oracle)")
    print(f"DSN: {DSN}\n")

    try:
        await demo_basic_connection()
        await demo_connection_pool()
        await demo_query_oracle_version()
        print("\n✅ Semua demo koneksi berhasil!\n")
    except oracledb.DatabaseError as e:
        print(f"\n❌ Database Error: {e}")
        print("Pastikan Oracle berjalan dan kredensial di .env sudah benar")


if __name__ == "__main__":
    asyncio.run(main())
