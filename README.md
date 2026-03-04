# Chapter 5 — Integrasi Oracle Database dengan FastAPI

Aplikasi FastAPI yang terhubung ke Oracle Database, mencakup:
- 🔌 **Driver Oracle Python** (`oracledb`)
- 🏊 **Connection Pooling**
- 💾 **Transaction** (commit & rollback)
- 🛡️ **Parameter Binding**
- 📋 **CRUD API** untuk resource Employee

---

## Prasyarat

- Python 3.11+
- Oracle Database berjalan di `localhost:1521` (service: `freepdb1`)
- User Oracle: `system`

---

## Struktur Project

```
test-koneksi-oracle/
├── app/
│   ├── __init__.py
│   ├── database.py          # Connection pool & dependency
│   ├── models.py            # Pydantic schemas
│   └── routers/
│       ├── __init__.py
│       └── employees.py     # CRUD endpoints
├── demo/
│   ├── demo_connection.py   # Demo: koneksi Oracle
│   ├── demo_transaction.py  # Demo: commit & rollback
│   └── demo_binding.py      # Demo: parameter binding
├── main.py                  # Entry point FastAPI
├── setup_db.sql             # SQL: buat tabel & data sample
├── .env                     # Konfigurasi (jangan di-commit!)
├── .env.example             # Template konfigurasi
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurasi .env

Edit file `.env` sesuai kredensial Oracle Anda:

```ini
ORACLE_USER=system
ORACLE_PASSWORD=your_password_here
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE=freepdb1
```

### 3. Setup database Oracle

Jalankan `setup_db.sql` di Oracle SQL*Plus atau DBeaver:

```sql
-- Di SQL*Plus:
@/path/to/setup_db.sql

-- Atau copy-paste isi file ke DBeaver SQL Editor
```

Script ini akan membuat:
- `SEQUENCE employees_seq` — auto-increment ID
- `TABLE employees` — tabel data karyawan
- 7 data sample karyawan

---

## Menjalankan Aplikasi

```bash
uvicorn main:app --reload
```

Akses:
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

---

## API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/` | Health check |
| GET | `/health` | Status connection pool |
| GET | `/api/v1/employees` | List semua karyawan |
| GET | `/api/v1/employees/{id}` | Get satu karyawan |
| POST | `/api/v1/employees` | Buat karyawan baru |
| PUT | `/api/v1/employees/{id}` | Update karyawan |
| DELETE | `/api/v1/employees/{id}` | Hapus karyawan |

### Contoh Request

**POST /api/v1/employees**
```json
{
    "nama": "Budi Santoso",
    "departemen": "Engineering",
    "jabatan": "Backend Developer",
    "gaji": 9000000,
    "tanggal_masuk": "2024-01-15"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Karyawan berhasil dibuat",
    "data": {
        "id": 1,
        "nama": "Budi Santoso",
        "departemen": "Engineering",
        "jabatan": "Backend Developer",
        "gaji": 9000000.0,
        "tanggal_masuk": "2024-01-15"
    },
    "meta": null
}
```

---

## Demo Scripts

Script edukasi untuk memahami konsep Oracle + Python:

### Demo 1: Koneksi

```bash
python demo/demo_connection.py
```

Menunjukkan:
- Perbedaan single connection vs connection pool
- Cara membaca info versi Oracle

### Demo 2: Transaction

```bash
python demo/demo_transaction.py
```

Menunjukkan:
- `COMMIT` — menyimpan perubahan permanen
- `ROLLBACK` — membatalkan perubahan
- `SAVEPOINT` — rollback sebagian transaksi

### Demo 3: Parameter Binding

```bash
python demo/demo_binding.py
```

Menunjukkan:
- ⚠️ Bahaya SQL Injection (string concatenation)
- ✅ Named binding (`:nama_param`)
- ✅ Positional binding (`:1, :2`)
- ✅ Batch binding (`executemany`)
- ✅ `RETURNING INTO` untuk dapat ID baru

---

## Konsep Penting

### Connection Pool

```python
# Pool dibuat SEKALI saat startup, dipakai semua request
pool = await oracledb.create_pool_async(
    user="system", password="...", dsn="localhost:1521/freepdb1",
    min=2,   # minimal 2 koneksi selalu aktif
    max=10,  # maksimal 10 koneksi bersamaan
    increment=1,
)
```

### Parameter Binding (BENAR ✅)

```python
# Gunakan :nama_parameter, bukan f-string!
await cursor.execute(
    "SELECT * FROM employees WHERE id = :emp_id",
    {"emp_id": 5}
)
```

### Transaction (commit & rollback)

```python
try:
    await cursor.execute("INSERT INTO ...", {...})
    await conn.commit()    # ✅ simpan permanen
except Exception:
    await conn.rollback()  # ❌ batalkan semua perubahan
    raise
```

---

## Troubleshooting

| Error | Solusi |
|-------|--------|
| `DPI-1047: Cannot locate a 64-bit Oracle Client` | `oracledb` bisa berjalan tanpa Oracle Client (`thin mode`), pastikan versi terbaru |
| `ORA-12541: TNS: no listener` | Pastikan Oracle berjalan dan port 1521 terbuka |
| `ORA-01017: invalid username/password` | Cek kredensial di `.env` |
| `ORA-00942: table or view does not exist` | Jalankan `setup_db.sql` terlebih dahulu |
