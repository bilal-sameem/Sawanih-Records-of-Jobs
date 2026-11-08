-- Reference only: Django creates this table for you from the Person model
-- (python manage.py makemigrations sawanih && python manage.py migrate).
CREATE TABLE sawanih_person (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name        VARCHAR(150) NOT NULL,
  father_name      VARCHAR(150) NOT NULL,
  grandfather_name VARCHAR(150) NOT NULL DEFAULT '',
  date_of_birth    DATE         NOT NULL,
  id_number        VARCHAR(30)  NOT NULL UNIQUE,      -- duplicate-ID check
  phone            VARCHAR(20)  NOT NULL,
  email            VARCHAR(254) NOT NULL DEFAULT '',
  address          TEXT         NOT NULL DEFAULT '',
  photo            VARCHAR(100) NOT NULL DEFAULT '',  -- file path under MEDIA_ROOT
  degree           VARCHAR(100) NOT NULL DEFAULT '',
  institution      VARCHAR(150) NOT NULL DEFAULT '',
  graduation_year  SMALLINT     NULL,
  job_title        VARCHAR(150) NOT NULL DEFAULT '',
  organization     VARCHAR(150) NOT NULL DEFAULT '',
  start_date       DATE         NULL,
  notes            TEXT         NOT NULL DEFAULT '',
  created_by_id    INTEGER      NULL REFERENCES auth_user(id) ON DELETE SET NULL,  -- audit
  created_at       DATETIME     NOT NULL                                           -- audit,
  updated_by_id    INTEGER      NULL REFERENCES auth_user(id) ON DELETE SET NULL,  -- audit (last edit)
  updated_at       DATETIME     NULL                                               -- audit (last edit)
);
