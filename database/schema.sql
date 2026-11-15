-- ============================================================
-- Skema database Somnipathy Lab (MySQL / MariaDB)
--
-- Cara pakai:
--   1. Nyalakan MySQL dari XAMPP Control Panel
--   2. Buka phpMyAdmin -> tab "SQL" -> tempel isi file ini -> Go
--      (atau: C:\xampp\mysql\bin\mysql.exe -u root < schema.sql)
--
-- Catatan: aplikasi juga bisa membuat tabel otomatis lewat
-- SQLAlchemy saat AUTO_CREATE_TABLES=1 di .env.
-- ============================================================

CREATE DATABASE IF NOT EXISTS somnipathy_lab
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE somnipathy_lab;

-- ------------------------------------------------------------
-- Setiap baris = satu kali proses deteksi
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detections (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_token CHAR(36)        NOT NULL COMMENT 'Token anonim pengunjung',
  input_data    JSON            NOT NULL COMMENT 'Salinan jawaban pengguna untuk audit',
  prediction    VARCHAR(64)     NOT NULL COMMENT 'Kelas hasil klasifikasi',
  confidence    DECIMAL(5,4)    NOT NULL COMMENT 'Keyakinan model 0.0000 - 1.0000',
  probabilities JSON            NULL     COMMENT 'Probabilitas semua kelas',
  model_version VARCHAR(32)     NOT NULL,
  created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_detections_created (created_at),
  KEY idx_detections_session (session_token),
  KEY idx_detections_prediction (prediction)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Rekomendasi hasil aturan untuk setiap deteksi
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_recommendations (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  detection_id BIGINT UNSIGNED NOT NULL,
  rule_id      VARCHAR(32)     NOT NULL COMMENT 'Contoh: DUR-01',
  category     VARCHAR(64)     NOT NULL,
  severity     VARCHAR(16)     NOT NULL COMMENT 'high | medium | low | info',
  title        VARCHAR(150)    NOT NULL,
  message      TEXT            NOT NULL,
  PRIMARY KEY (id),
  KEY idx_recommendations_detection (detection_id),
  CONSTRAINT fk_recommendation_detection
    FOREIGN KEY (detection_id) REFERENCES detections (id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
