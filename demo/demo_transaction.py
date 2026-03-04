"""
demo/demo_transaction.py
========================
Demo: Transaction — commit dan rollback di Oracle.

Jalankan dengan:
    python demo/demo_transaction.py

Konsep:
- BEGIN TRANSACTION (implicit di Oracle)
- COMMIT   → simpan perubahan permanen
- ROLLBACK → batalkan perubahan, kembalikan ke state sebelumnya
- Oracle mode: autocommit = False by default
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


async def get_employee_count(cursor) -> int:
    """Helper: hitung jumlah baris di tabel employees."""
    await cursor.execute("SELECT COUNT(*) FROM employees")
    row = await cursor.fetchone()
    return row[0]


async def demo_commit():
    """
    Demo COMMIT — perubahan disimpan permanen.
    """
    print("\n" + "="*60)
    print("DEMO COMMIT — perubahan permanen")
    print("="*60)

    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()

    count_before = await get_employee_count(cursor)
    print(f"[SEBELUM] Jumlah karyawan: {count_before}")

    # INSERT data baru
    print("\n[ACTION] Memasukkan karyawan test...")
    await cursor.execute(
        """
        INSERT INTO employees (id, nama, departemen, jabatan, gaji)
        VALUES (employees_seq.NEXTVAL, :nama, :departemen, :jabatan, :gaji)
        """,
        {
            "nama": "Test COMMIT",
            "departemen": "Test",
            "jabatan": "Test Engineer",
            "gaji": 5000000,
        },
    )

    # Cek dalam transaksi yang sama (belum commit — tapi session ini bisa lihat)
    count_during = await get_employee_count(cursor)
    print(f"[SELAMA TRANSAKSI] Jumlah karyawan (dalam session): {count_during}")

    # ✅ COMMIT — simpan ke database
    await conn.commit()
    print("\n✅ COMMIT berhasil!")

    count_after = await get_employee_count(cursor)
    print(f"[SETELAH COMMIT] Jumlah karyawan: {count_after}")
    print("→ Data berhasil tersimpan permanen")

    # Cleanup: hapus data test
    await cursor.execute("DELETE FROM employees WHERE nama = 'Test COMMIT'")
    await conn.commit()
    print("[CLEANUP] Data test dihapus")

    cursor.close()
    await conn.close()


async def demo_rollback():
    """
    Demo ROLLBACK — perubahan dibatalkan.
    """
    print("\n" + "="*60)
    print("DEMO ROLLBACK — perubahan dibatalkan")
    print("="*60)

    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()

    count_before = await get_employee_count(cursor)
    print(f"[SEBELUM] Jumlah karyawan: {count_before}")

    # INSERT tapi kita akan rollback
    print("\n[ACTION] Memasukkan karyawan 'ghost' (akan di-rollback)...")
    await cursor.execute(
        """
        INSERT INTO employees (id, nama, departemen, jabatan, gaji)
        VALUES (employees_seq.NEXTVAL, :nama, :departemen, :jabatan, :gaji)
        """,
        {
            "nama": "Ghost Employee",
            "departemen": "Ghost Dept",
            "jabatan": "Ghost Worker",
            "gaji": 1,
        },
    )

    count_during = await get_employee_count(cursor)
    print(f"[SELAMA TRANSAKSI] Jumlah karyawan (dalam session): {count_during}")

    # Simulasi error terjadi → ROLLBACK
    print("\n[SIMULASI] Terjadi error! Jalankan ROLLBACK...")
    await conn.rollback()
    print("❌ ROLLBACK berhasil!")

    count_after = await get_employee_count(cursor)
    print(f"[SETELAH ROLLBACK] Jumlah karyawan: {count_after}")
    print("→ Data 'ghost' tidak tersimpan, jumlah sama seperti awal")

    cursor.close()
    await conn.close()


async def demo_savepoint():
    """
    Demo SAVEPOINT — rollback sebagian transaksi.
    Oracle mendukung SAVEPOINT untuk kontrol yang lebih granular.
    """
    print("\n" + "="*60)
    print("DEMO SAVEPOINT — rollback sebagian")
    print("="*60)

    conn = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()

    count_before = await get_employee_count(cursor)
    print(f"[SEBELUM] Jumlah karyawan: {count_before}")

    # INSERT pertama — VALID
    await cursor.execute(
        """
        INSERT INTO employees (id, nama, departemen, jabatan, gaji)
        VALUES (employees_seq.NEXTVAL, 'Budi Valid', 'IT', 'Developer', 8000000)
        """
    )
    print("[INSERT 1] Budi Valid → OK")

    # Set SAVEPOINT setelah insert pertama
    await cursor.execute("SAVEPOINT after_first_insert")
    print("[SAVEPOINT] Disimpan setelah insert pertama")

    # INSERT kedua — akan di-rollback ke savepoint
    await cursor.execute(
        """
        INSERT INTO employees (id, nama, departemen, jabatan, gaji)
        VALUES (employees_seq.NEXTVAL, 'Rudi Gagal', 'Unknown', 'Unknown', -1)
        """
    )
    print("[INSERT 2] Rudi Gagal → akan di-rollback ke savepoint")

    count_during = await get_employee_count(cursor)
    print(f"[SELAMA] Jumlah sementara: {count_during}")

    # ROLLBACK ke savepoint (hanya batalkan insert kedua)
    await cursor.execute("ROLLBACK TO SAVEPOINT after_first_insert")
    print("[ROLLBACK TO SAVEPOINT] Insert kedua dibatalkan")

    # COMMIT hanya menyimpan insert pertama
    await conn.commit()
    count_after = await get_employee_count(cursor)
    print(f"[SETELAH] Jumlah karyawan: {count_after}")
    print("→ Hanya 'Budi Valid' yang tersimpan")

    # Cleanup
    await cursor.execute("DELETE FROM employees WHERE nama = 'Budi Valid'")
    await conn.commit()
    print("[CLEANUP] Data test dihapus")

    cursor.close()
    await conn.close()


async def main():
    print("\n💾 DEMO TRANSACTION ORACLE DATABASE")
    print("Autocommit Oracle: OFF by default (berbeda dari MySQL!)\n")

    conn_test = await oracledb.connect_async(user=USER, password=PASSWORD, dsn=DSN)
    print(f"Autocommit status: {conn_test.autocommit}")
    await conn_test.close()

    try:
        await demo_commit()
        await demo_rollback()
        await demo_savepoint()
        print("\n✅ Semua demo transaction selesai!\n")
    except oracledb.DatabaseError as e:
        print(f"\n❌ Database Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
