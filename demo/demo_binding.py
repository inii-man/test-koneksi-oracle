"""
demo/demo_binding.py
====================
Demo: Parameter Binding vs String Concatenation

Jalankan dengan:
    python demo/demo_binding.py

Konsep:
- Mengapa parameter binding WAJIB digunakan
- Bahaya SQL Injection dengan string concatenation
- Named binding (:nama) vs Positional binding (:1, :2)
- Batch binding (executemany)
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


async def demo_sql_injection_risk():
    """
    Demo: Bahaya String Concatenation (SQL Injection).
    JANGAN lakukan ini di production!
    """
    print("\n" + "="*60)
    print("⚠️  DEMO SQL INJECTION RISK (Cara SALAH!)")
    print("="*60)

    # Misalkan ini input dari user yang jahat (malicious input)
    nama_user = "Hacker' OR '1'='1"  # SQL Injection payload

    # CARA SALAH: string concatenation langsung di SQL
    sql_berbahaya = f"""
        SELECT id, nama, departemen FROM employees
        WHERE nama = '{nama_user}'
    """
    print("\n[SQL yang dihasilkan dari string concatenation]:")
    print(sql_berbahaya)
    print("\n⚠️  Query di atas bisa mengembalikan SEMUA data!")
    print("   Karena kondisi \"'1'='1'\" selalu TRUE")
    print("\n❌ JANGAN pernah gunakan f-string atau .format() untuk SQL query!")


async def demo_named_binding():
    """
    Demo: Named Parameter Binding (:nama_parameter)
    Ini cara yang BENAR dan AMAN.
    """
    print("\n" + "="*60)
    print("✅ DEMO NAMED PARAMETER BINDING (Cara BENAR)")
    print("="*60)

    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()

    # Input yang sama tapi pakai binding
    nama_user = "Hacker' OR '1'='1"

    print(f"\n[Input user]: {nama_user}")
    print("\n[SQL dengan Named Binding]:")
    print("  SELECT id, nama FROM employees WHERE nama = :nama")
    print("  {'nama': repr(nama_user)}")

    # ✅ AMAN: Oracle memperlakukan nilai sebagai DATA, bukan SQL
    await cursor.execute(
        "SELECT id, nama FROM employees WHERE nama = :nama",
        {"nama": nama_user},
    )
    rows = await cursor.fetchall()
    print(f"\n[Hasil]: {len(rows)} baris ditemukan")
    print("→ Payload SQL Injection tidak berpengaruh karena nilai diperlakukan sebagai string literal")

    cursor.close()
    await conn.close()


async def demo_positional_binding():
    """
    Demo: Positional Parameter Binding (:1, :2, ...)
    Alternatif dari named binding, berguna untuk query dinamis.
    """
    print("\n" + "="*60)
    print("✅ DEMO POSITIONAL PARAMETER BINDING")
    print("="*60)

    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()

    gaji_min = 5_000_000
    gaji_max = 15_000_000
    departemen = "Engineering"

    print(f"\n[Parameter]: gaji_min={gaji_min}, gaji_max={gaji_max}, dept={departemen}")
    print("[SQL]:")
    print("  SELECT nama, gaji FROM employees")
    print("  WHERE gaji BETWEEN :1 AND :2 AND departemen = :3")

    await cursor.execute(
        """
        SELECT nama, jabatan, gaji FROM employees
        WHERE gaji BETWEEN :1 AND :2
        AND departemen = :3
        ORDER BY gaji DESC
        """,
        [gaji_min, gaji_max, departemen],  # Positional list
    )
    rows = await cursor.fetchall()
    print(f"\n[Hasil] {len(rows)} karyawan:")
    for row in rows:
        print(f"  - {row[0]:20} | {row[1]:20} | Rp {row[2]:>12,.0f}")

    cursor.close()
    await conn.close()


async def demo_batch_binding():
    """
    Demo: Batch Binding dengan executemany()
    Sangat efisien untuk INSERT banyak data sekaligus.
    """
    print("\n" + "="*60)
    print("✅ DEMO BATCH BINDING (executemany)")
    print("="*60)

    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()

    # Data untuk batch insert
    batch_data = [
        {"nama": "Batch User 1", "departemen": "IT",       "jabatan": "Developer",  "gaji": 7000000},
        {"nama": "Batch User 2", "departemen": "Finance",  "jabatan": "Analyst",    "gaji": 6500000},
        {"nama": "Batch User 3", "departemen": "HR",       "jabatan": "Recruiter",  "gaji": 6000000},
        {"nama": "Batch User 4", "departemen": "IT",       "jabatan": "DevOps",     "gaji": 8000000},
        {"nama": "Batch User 5", "departemen": "Marketing","jabatan": "Strategist", "gaji": 7500000},
    ]

    print(f"\n[ACTION] Insert {len(batch_data)} karyawan sekaligus dengan executemany...")

    import time
    start = time.time()

    # executemany: satu kali round-trip ke Oracle untuk semua data
    await cursor.executemany(
        """
        INSERT INTO employees (id, nama, departemen, jabatan, gaji)
        VALUES (employees_seq.NEXTVAL, :nama, :departemen, :jabatan, :gaji)
        """,
        batch_data,
    )
    await conn.commit()

    elapsed = time.time() - start
    print(f"✅ {len(batch_data)} data berhasil diinsert dalam {elapsed:.3f} detik")
    print("→ executemany jauh lebih cepat dari loop + execute satu per satu!")

    # Cleanup
    print("\n[CLEANUP] Menghapus data batch test...")
    await cursor.execute(
        "DELETE FROM employees WHERE nama LIKE 'Batch User%'"
    )
    deleted = cursor.rowcount
    await conn.commit()
    print(f"✅ {deleted} data test dihapus")

    cursor.close()
    await conn.close()


async def demo_output_variable():
    """
    Demo: Membaca nilai OUTPUT dari INSERT menggunakan RETURNING INTO.
    Berguna untuk mendapatkan ID yang baru diinsert tanpa query tambahan.
    """
    print("\n" + "="*60)
    print("✅ DEMO RETURNING INTO (mendapat ID baru)")
    print("="*60)

    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()

    # Variabel output Oracle
    new_id = cursor.var(oracledb.NUMBER)

    await cursor.execute(
        """
        INSERT INTO employees (id, nama, departemen, jabatan, gaji)
        VALUES (employees_seq.NEXTVAL, :nama, :departemen, :jabatan, :gaji)
        RETURNING id INTO :new_id
        """,
        {
            "nama": "Return Demo",
            "departemen": "Demo",
            "jabatan": "Demo Engineer",
            "gaji": 5000000,
            "new_id": new_id,
        },
    )
    await conn.commit()
    print(f"\n✅ Data berhasil diinsert!")
    print(f"   ID baru: {int(new_id.getvalue()[0])}")
    print("→ Tidak perlu query SELECT terpisah untuk mendapat ID-nya!")

    # Cleanup
    await cursor.execute(
        "DELETE FROM employees WHERE nama = 'Return Demo'"
    )
    await conn.commit()
    print("[CLEANUP] Data test dihapus")

    cursor.close()
    await conn.close()


async def main():
    print("\n🛡️  DEMO PARAMETER BINDING")
    print("Mencegah SQL Injection dan meningkatkan performa query\n")

    try:
        await demo_sql_injection_risk()
        await demo_named_binding()
        await demo_positional_binding()
        await demo_batch_binding()
        await demo_output_variable()
        print("\n✅ Semua demo parameter binding selesai!\n")
    except oracledb.DatabaseError as e:
        print(f"\n❌ Database Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
