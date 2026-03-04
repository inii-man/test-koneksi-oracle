"""
init_db.py
==========
Script untuk membuat tabel EMPLOYEES dan SEQUENCE di Oracle.

Jalankan SEKALI sebelum menjalankan server:
    python init_db.py
"""

import asyncio
import oracledb
from dotenv import load_dotenv
import os

load_dotenv()

DSN = (
    f"{os.getenv('ORACLE_HOST', 'localhost')}:"
    f"{os.getenv('ORACLE_PORT', '1521')}/"
    f"{os.getenv('ORACLE_SERVICE', 'freepdb1')}"
)
USER     = os.getenv("ORACLE_USER", "system")
PASSWORD = os.getenv("ORACLE_PASSWORD", "oracle")


async def main():
    print(f"🔌 Connecting to Oracle: {DSN} as {USER}...")
    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()
    print("✅ Connected!\n")

    # ─────────────────────────────
    # DROP jika sudah ada (opsional)
    # ─────────────────────────────
    print("🗑️  Dropping existing objects if any...")
    for drop_sql, label in [
        ("DROP TABLE employees PURGE", "table employees"),
        ("DROP SEQUENCE employees_seq", "sequence employees_seq"),
    ]:
        try:
            await cursor.execute(drop_sql)
            print(f"   Dropped {label}")
        except oracledb.DatabaseError:
            print(f"   {label} not found (skip)")

    # ─────────────────────────────
    # CREATE SEQUENCE
    # ─────────────────────────────
    print("\n📋 Creating sequence employees_seq...")
    await cursor.execute("""
        CREATE SEQUENCE employees_seq
            START WITH 1
            INCREMENT BY 1
            NOCACHE
            NOCYCLE
    """)
    print("   ✅ Sequence created")

    # ─────────────────────────────
    # CREATE TABLE
    # ─────────────────────────────
    print("\n📋 Creating table employees...")
    await cursor.execute("""
        CREATE TABLE employees (
            id             NUMBER(10)      PRIMARY KEY,
            nama           VARCHAR2(100)   NOT NULL,
            departemen     VARCHAR2(50)    NOT NULL,
            jabatan        VARCHAR2(100)   NOT NULL,
            gaji           NUMBER(15, 2)   NOT NULL,
            tanggal_masuk  DATE            DEFAULT SYSDATE,
            created_at     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ Table created")

    # ─────────────────────────────
    # INSERT SAMPLE DATA
    # ─────────────────────────────
    print("\n📥 Inserting sample data...")
    sample_data = [
        ("Budi Santoso",  "Engineering", "Backend Developer",   9000000,  "15-MAR-22"),
        ("Siti Rahayu",   "Engineering", "Frontend Developer",  8500000,  "01-JUL-22"),
        ("Ahmad Fauzi",   "Finance",     "Financial Analyst",   7500000,  "20-NOV-21"),
        ("Dewi Lestari",  "HR",          "HR Manager",          10000000, "10-MAY-20"),
        ("Rudi Hartono",  "Engineering", "DevOps Engineer",     11000000, "30-APR-21"),
        ("Maya Indira",   "Marketing",   "Marketing Strategist",8000000,  "15-JAN-23"),
        ("Hendra Wijaya", "Engineering", "Tech Lead",           15000000, "01-AUG-19"),
    ]

    for nama, dept, jabatan, gaji, tgl in sample_data:
        await cursor.execute(
            """
            INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
            VALUES (employees_seq.NEXTVAL, :1, :2, :3, :4, TO_DATE(:5, 'DD-MON-YY'))
            """,
            [nama, dept, jabatan, gaji, tgl],
        )

    await conn.commit()
    print(f"   ✅ {len(sample_data)} data sample berhasil diinsert")

    # ─────────────────────────────
    # VERIFIKASI
    # ─────────────────────────────
    print("\n📊 Verifikasi data:")
    await cursor.execute(
        "SELECT id, nama, departemen, gaji FROM employees ORDER BY id"
    )
    rows = await cursor.fetchall()
    print(f"   {'ID':<5} {'Nama':<20} {'Departemen':<15} {'Gaji':>12}")
    print("   " + "-"*55)
    for row in rows:
        print(f"   {row[0]:<5} {row[1]:<20} {row[2]:<15} Rp {row[3]:>10,.0f}")

    print(f"\n✅ Setup selesai! Total {len(rows)} karyawan siap di database.")
    print("🚀 Sekarang jalankan: uvicorn main:app --reload\n")

    cursor.close()
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
