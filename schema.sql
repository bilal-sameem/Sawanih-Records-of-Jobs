-- SQLite (for Postgres: use SERIAL/BIGINT identity, BOOLEAN, TIMESTAMPTZ DEFAULT now())
CREATE TABLE IF NOT EXISTS sawanih (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  slug       TEXT NOT NULL UNIQUE,
  title      TEXT NOT NULL,
  subtitle   TEXT NOT NULL DEFAULT '',
  intro      TEXT NOT NULL DEFAULT '',
  language   TEXT NOT NULL DEFAULT 'ps',
  published  INTEGER NOT NULL DEFAULT 0 CHECK (published IN (0,1)),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sawanih_sections (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  sawanih_id INTEGER NOT NULL REFERENCES sawanih(id) ON DELETE CASCADE,
  heading    TEXT NOT NULL,
  body       TEXT NOT NULL DEFAULT '',
  position   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS timeline_events (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  sawanih_id        INTEGER NOT NULL REFERENCES sawanih(id) ON DELETE CASCADE,
  date_label        TEXT NOT NULL,          -- free text, e.g. "۱۳۸۳" or "1990–1994"
  event_title       TEXT NOT NULL,
  event_description TEXT NOT NULL DEFAULT '',
  position          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS quotes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  sawanih_id  INTEGER NOT NULL REFERENCES sawanih(id) ON DELETE CASCADE,
  text        TEXT NOT NULL,
  attribution TEXT NOT NULL DEFAULT '',
  position    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sections_parent ON sawanih_sections(sawanih_id, position);
CREATE INDEX IF NOT EXISTS idx_events_parent   ON timeline_events(sawanih_id, position);
CREATE INDEX IF NOT EXISTS idx_quotes_parent   ON quotes(sawanih_id, position);
