"""
app/routers/employees.py
========================
CRUD endpoints untuk resource Employee.

Konsep yang dipelajari:
- Parameter Binding (mencegah SQL Injection)
- Transaction (commit & rollback)
- Dependency Injection dengan Depends(get_db)
- Error handling dengan HTTPException
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.database import get_db
from app.models import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    ResponseEnvelope,
)

router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])

# Type alias agar lebih singkat
DB = Annotated[tuple, Depends(get_db)]


# ─────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────

def row_to_dict(row, cursor) -> dict:
    """Mengubah row Oracle menjadi dict berdasarkan nama kolom cursor."""
    columns = [col[0].lower() for col in cursor.description]
    return dict(zip(columns, row))


async def find_employee_or_404(employee_id: int, cursor) -> dict:
    """
    Cari employee berdasarkan ID. Raise 404 jika tidak ditemukan.

    Parameter Binding: gunakan :employee_id bukan f-string
    untuk mencegah SQL Injection.
    """
    await cursor.execute(
        """
        SELECT id, nama, departemen, jabatan, gaji, tanggal_masuk
        FROM employees
        WHERE id = :employee_id
        """,
        {"employee_id": employee_id},   # ← PARAMETER BINDING
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee dengan id={employee_id} tidak ditemukan",
        )
    return row_to_dict(row, cursor)


# ─────────────────────────────────────────────────────────────
# GET /api/v1/employees  — list semua karyawan
# ─────────────────────────────────────────────────────────────
@router.get("/", response_model=ResponseEnvelope, summary="Ambil semua karyawan")
async def list_employees(db: DB):
    """
    Mengambil seluruh data karyawan dari tabel Oracle.

    Tidak ada transaction eksplisit karena ini hanya operasi baca (SELECT).
    """
    cursor, _ = db
    await cursor.execute(
        "SELECT id, nama, departemen, jabatan, gaji, tanggal_masuk FROM employees ORDER BY id"
    )
    rows = await cursor.fetchall()
    data = [row_to_dict(row, cursor) for row in rows]
    return ResponseEnvelope(
        success=True,
        message=f"{len(data)} karyawan ditemukan",
        data=data,
        meta={"total": len(data)},
    )


# ─────────────────────────────────────────────────────────────
# GET /api/v1/employees/{employee_id}  — ambil satu karyawan
# ─────────────────────────────────────────────────────────────
@router.get("/{employee_id}", response_model=ResponseEnvelope, summary="Ambil satu karyawan")
async def get_employee(employee_id: int, db: DB):
    """
    Mengambil data satu karyawan berdasarkan ID.

    Parameter Binding: :employee_id di SQL query.
    """
    cursor, _ = db
    employee = await find_employee_or_404(employee_id, cursor)
    return ResponseEnvelope(success=True, message="OK", data=employee)


# ─────────────────────────────────────────────────────────────
# POST /api/v1/employees  — buat karyawan baru
# ─────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=ResponseEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Buat karyawan baru",
)
async def create_employee(payload: EmployeeCreate, db: DB):
    """
    Membuat karyawan baru dan menyimpan ke Oracle.

    TRANSACTION:
    - Jika INSERT berhasil → conn.commit()
    - Jika ada error → conn.rollback() (data tidak tersimpan)

    PARAMETER BINDING:
    Semua nilai payload dikirim lewat dict, bukan string concatenation.
    Ini mencegah SQL Injection.
    """
    cursor, conn = db
    try:
        # Gunakan SEQUENCE untuk auto-increment ID di Oracle
        await cursor.execute(
            """
            INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
            VALUES (employees_seq.NEXTVAL, :nama, :departemen, :jabatan, :gaji, :tanggal_masuk)
            """,
            {                                          # ← PARAMETER BINDING
                "nama": payload.nama,
                "departemen": payload.departemen,
                "jabatan": payload.jabatan,
                "gaji": payload.gaji,
                "tanggal_masuk": payload.tanggal_masuk,
            },
        )

        # Ambil ID yang baru dibuat
        await cursor.execute("SELECT employees_seq.CURRVAL FROM dual")
        row = await cursor.fetchone()
        new_id = row[0]

        # ✅ COMMIT — simpan perubahan permanen ke database
        await conn.commit()
        print(f"[DB] ✅ COMMIT — Employee baru id={new_id} berhasil disimpan")

        # Ambil data lengkap untuk response
        new_employee = await find_employee_or_404(new_id, cursor)
        return ResponseEnvelope(
            success=True,
            message="Karyawan berhasil dibuat",
            data=new_employee,
        )

    except Exception as e:
        # ❌ ROLLBACK — batalkan perubahan yang belum di-commit
        await conn.rollback()
        print(f"[DB] ❌ ROLLBACK — Gagal membuat employee: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menyimpan data: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────
# PUT /api/v1/employees/{employee_id}  — update karyawan
# ─────────────────────────────────────────────────────────────
@router.put("/{employee_id}", response_model=ResponseEnvelope, summary="Update karyawan")
async def update_employee(employee_id: int, payload: EmployeeUpdate, db: DB):
    """
    Mengupdate field karyawan yang dikirim saja (partial update).

    TRANSACTION + PARAMETER BINDING:
    Query dibangun secara dinamis berdasarkan field yang tidak None,
    tapi semua nilai tetap menggunakan binding (:param) bukan f-string.
    """
    cursor, conn = db
    # Cek employee ada
    await find_employee_or_404(employee_id, cursor)

    # Bangun SET clause secara dinamis — hanya field yang dikirim
    update_fields = {}
    if payload.nama is not None:
        update_fields["nama"] = payload.nama
    if payload.departemen is not None:
        update_fields["departemen"] = payload.departemen
    if payload.jabatan is not None:
        update_fields["jabatan"] = payload.jabatan
    if payload.gaji is not None:
        update_fields["gaji"] = payload.gaji
    if payload.tanggal_masuk is not None:
        update_fields["tanggal_masuk"] = payload.tanggal_masuk

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak ada field yang diupdate",
        )

    # SET clause: "nama = :nama, gaji = :gaji, ..."
    set_clause = ", ".join(f"{col} = :{col}" for col in update_fields)
    update_fields["employee_id"] = employee_id  # tambahkan untuk WHERE

    try:
        await cursor.execute(
            f"UPDATE employees SET {set_clause} WHERE id = :employee_id",
            update_fields,   # ← PARAMETER BINDING
        )

        # ✅ COMMIT
        await conn.commit()
        print(f"[DB] ✅ COMMIT — Employee id={employee_id} berhasil diupdate")

        updated = await find_employee_or_404(employee_id, cursor)
        return ResponseEnvelope(
            success=True,
            message=f"Employee id={employee_id} berhasil diupdate",
            data=updated,
        )

    except Exception as e:
        # ❌ ROLLBACK
        await conn.rollback()
        print(f"[DB] ❌ ROLLBACK — Gagal update employee: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengupdate data: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────
# DELETE /api/v1/employees/{employee_id}  — hapus karyawan
# ─────────────────────────────────────────────────────────────
@router.delete(
    "/{employee_id}",
    response_model=ResponseEnvelope,
    summary="Hapus karyawan",
)
async def delete_employee(employee_id: int, db: DB):
    """
    Menghapus karyawan berdasarkan ID.

    TRANSACTION + PARAMETER BINDING.
    """
    cursor, conn = db
    # Cek employee ada
    employee = await find_employee_or_404(employee_id, cursor)

    try:
        await cursor.execute(
            "DELETE FROM employees WHERE id = :employee_id",
            {"employee_id": employee_id},   # ← PARAMETER BINDING
        )

        # ✅ COMMIT
        await conn.commit()
        print(f"[DB] ✅ COMMIT — Employee id={employee_id} berhasil dihapus")

        return ResponseEnvelope(
            success=True,
            message=f"Employee id={employee_id} ({employee['nama']}) berhasil dihapus",
            data=None,
        )

    except Exception as e:
        # ❌ ROLLBACK
        await conn.rollback()
        print(f"[DB] ❌ ROLLBACK — Gagal hapus employee: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menghapus data: {str(e)}",
        )
