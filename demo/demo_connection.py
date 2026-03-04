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
    Demo 2: Connection Pool + Pool Health Check
    Pool lebih efisien karena koneksi dibuat sekali dan dipakai bersama.

    Catatan: AsyncConnectionPool (oracledb v2.x) tidak expose .opened/.busy/.free
    secara langsung. Kita track manual menggunakan counter.
    """
    print("\n" + "="*60)
    print("DEMO 2: Connection Pool")
    print("="*60)

    # Buat pool dengan min=2, max=5 koneksi
    pool = oracledb.create_pool_async(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN,
        min=2,
        max=5,
        increment=1,
    )
    print(f"✅ Pool dibuat!")

    # ── POOL HEALTH CHECK ────────────────────────────────────
    # Manual tracking: opened/busy/queue tidak tersedia di v2.x AsyncConnectionPool
    opened = 0          # jumlah koneksi yang telah dibuat ke Oracle
    busy   = 0          # sedang dipakai oleh request
    queued = 0          # request yang sedang antri menunggu koneksi kosong

    # Buka beberapa koneksi simultan untuk demonstrasi
    async def simulate_request(req_id: int):
        nonlocal opened, busy, queued
        queued += 1
        async with pool.acquire() as conn:
            queued -= 1
            opened += 1
            busy   += 1
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT :req_id || ': query dari pool' FROM dual",
                    {"req_id": req_id},
                )
                row = await cursor.fetchone()
                print(f"   Request #{req_id} → {row[0]}")
                await asyncio.sleep(0.05)   # simulasi query lambat
            busy   -= 1

    # Jalankan 3 request bersamaan
    print("\n   Menjalankan 3 request serentak ke pool...")
    await asyncio.gather(
        simulate_request(1),
        simulate_request(2),
        simulate_request(3),
    )

    print("\nPool Health Check:")
    print(f"✅ Opened connections : {opened}")                # Total conn terbuka
    print(f"✅ Busy (in use)      : {busy}")                  # Sedang dipakai
    print(f"✅ Available          : {opened - busy}")         # Siap dipakai
    print(f"✅ Max allowed        : {pool.max}")
    print(f"✅ Min guaranteed     : {pool.min}")
    print(f"✅ Queue requests     : {queued}")                 # Antrian menunggu
    # ─────────────────────────────────────────────────────────

    await pool.close()
    print("\n🔌 Pool ditutup")


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
