-- ============================================================
-- setup_db.sql
-- Script untuk membuat tabel dan sequence di Oracle
-- Jalankan di Oracle SQL*Plus atau DBeaver sebagai user SYSTEM
-- ============================================================

-- ──────────────────────────────────────────
-- 1. BUAT SEQUENCE untuk auto-increment ID
-- ──────────────────────────────────────────
-- DROP SEQUENCE employees_seq;  -- Hapus komentar jika ingin reset
CREATE SEQUENCE employees_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- ──────────────────────────────────────────
-- 2. BUAT TABEL EMPLOYEES
-- ──────────────────────────────────────────
-- DROP TABLE employees;  -- Hapus komentar jika ingin recreate
CREATE TABLE employees (
    id             NUMBER(10)      PRIMARY KEY,
    nama           VARCHAR2(100)   NOT NULL,
    departemen     VARCHAR2(50)    NOT NULL,
    jabatan        VARCHAR2(100)   NOT NULL,
    gaji           NUMBER(15, 2)   NOT NULL,
    tanggal_masuk  DATE            DEFAULT SYSDATE,
    created_at     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────
-- 3. COMMENT KOLOM (dokumentasi)
-- ──────────────────────────────────────────
COMMENT ON TABLE employees IS 'Tabel data karyawan - Chapter 5 FastAPI Oracle';
COMMENT ON COLUMN employees.id IS 'ID unik karyawan, menggunakan sequence';
COMMENT ON COLUMN employees.nama IS 'Nama lengkap karyawan';
COMMENT ON COLUMN employees.departemen IS 'Nama departemen karyawan';
COMMENT ON COLUMN employees.jabatan IS 'Jabatan/posisi karyawan';
COMMENT ON COLUMN employees.gaji IS 'Gaji bulanan dalam Rupiah';
COMMENT ON COLUMN employees.tanggal_masuk IS 'Tanggal mulai bekerja';

-- ──────────────────────────────────────────
-- 4. DATA SAMPLE
-- ──────────────────────────────────────────
INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
VALUES (employees_seq.NEXTVAL, 'Budi Santoso', 'Engineering', 'Backend Developer', 9000000, DATE '2022-03-15');

INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
VALUES (employees_seq.NEXTVAL, 'Siti Rahayu', 'Engineering', 'Frontend Developer', 8500000, DATE '2022-07-01');

INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
VALUES (employees_seq.NEXTVAL, 'Ahmad Fauzi', 'Finance', 'Financial Analyst', 7500000, DATE '2021-11-20');

INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
VALUES (employees_seq.NEXTVAL, 'Dewi Lestari', 'HR', 'HR Manager', 10000000, DATE '2020-05-10');

INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
VALUES (employees_seq.NEXTVAL, 'Rudi Hartono', 'Engineering', 'DevOps Engineer', 11000000, DATE '2021-04-30');

INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
VALUES (employees_seq.NEXTVAL, 'Maya Indira', 'Marketing', 'Marketing Strategist', 8000000, DATE '2023-01-15');

INSERT INTO employees (id, nama, departemen, jabatan, gaji, tanggal_masuk)
VALUES (employees_seq.NEXTVAL, 'Hendra Wijaya', 'Engineering', 'Tech Lead', 15000000, DATE '2019-08-01');

COMMIT;

-- ──────────────────────────────────────────
-- 5. VERIFIKASI
-- ──────────────────────────────────────────
SELECT id, nama, departemen, jabatan, gaji
FROM employees
ORDER BY id;

-- Tampilkan jumlah data
SELECT COUNT(*) AS total_karyawan FROM employees;

SELECT 'Setup berhasil! Tabel employees siap digunakan.' AS status FROM dual;
