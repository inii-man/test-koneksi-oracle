"""
app/models.py
=============
Pydantic schemas untuk Employee.

Konsep yang dipelajari:
- Pydantic v2 BaseModel
- Pemisahan schema: Create, Update, Response
- Validasi otomatis dan type hints
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ─────────────────────────────────────────────
# Base Schema — field yang sama di semua operasi
# ─────────────────────────────────────────────
class EmployeeBase(BaseModel):
    nama: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nama lengkap karyawan",
        examples=["Budi Santoso"]
    )
    departemen: str = Field(
        ...,
        max_length=50,
        description="Nama departemen",
        examples=["Engineering"]
    )
    jabatan: str = Field(
        ...,
        max_length=100,
        description="Jabatan karyawan",
        examples=["Backend Developer"]
    )
    gaji: float = Field(
        ...,
        gt=0,
        description="Gaji bulanan (harus lebih dari 0)",
        examples=[8500000.0]
    )
    tanggal_masuk: Optional[date] = Field(
        default=None,
        description="Tanggal mulai bekerja (format: YYYY-MM-DD)",
        examples=["2024-01-15"]
    )


# ─────────────────────────────────────────────
# CREATE — dipakai untuk POST /employees
# ─────────────────────────────────────────────
class EmployeeCreate(EmployeeBase):
    """Schema untuk membuat karyawan baru. Semua field wajib diisi."""
    pass


# ─────────────────────────────────────────────
# UPDATE — dipakai untuk PUT /employees/{id}
# ─────────────────────────────────────────────
class EmployeeUpdate(BaseModel):
    """
    Schema untuk update karyawan. Semua field bersifat opsional
    sehingga client hanya perlu mengirim field yang berubah.
    """
    nama: Optional[str] = Field(None, min_length=2, max_length=100)
    departemen: Optional[str] = Field(None, max_length=50)
    jabatan: Optional[str] = Field(None, max_length=100)
    gaji: Optional[float] = Field(None, gt=0)
    tanggal_masuk: Optional[date] = None


# ─────────────────────────────────────────────
# RESPONSE — dipakai untuk API response
# ─────────────────────────────────────────────
class EmployeeResponse(EmployeeBase):
    """Schema untuk response API. Menambahkan field id."""
    id: int = Field(..., description="ID unik karyawan dari database")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# RESPONSE ENVELOPE — wrapper standar API
# ─────────────────────────────────────────────
class ResponseEnvelope(BaseModel):
    """
    Standar response untuk semua endpoint.
    Konsisten dengan pattern yang sudah ada di project sebelumnya.
    """
    success: bool = True
    message: str = "OK"
    data: Optional[object] = None
    meta: Optional[dict] = None
