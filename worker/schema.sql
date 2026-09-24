-- D1 database "blokvolt" (binding DB in the Pages project). Paste into the D1 console to create or update.
-- Drivers' check-ins at public chargers: status, optional rating 1-5, optional short comment.
CREATE TABLE IF NOT EXISTS checkins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  st TEXT NOT NULL,              -- station id from /assets/map/punjaci.json
  s TEXT NOT NULL,               -- ok | problem | broken | missing
  r INTEGER,                     -- rating 1..5 or NULL
  c TEXT,                        -- comment (<= 500 chars) or NULL
  n TEXT,                        -- nickname (<= 40 chars) or NULL
  cs TEXT NOT NULL DEFAULT 'none', -- comment state: none | ok | pending | hidden
  at INTEGER NOT NULL,           -- unix seconds
  lang TEXT,
  ip TEXT,                       -- sha-256 of ip + day (not reversible, rotates daily)
  rep INTEGER NOT NULL DEFAULT 0 -- abuse reports
);
CREATE INDEX IF NOT EXISTS checkins_st ON checkins (st, at);
CREATE INDEX IF NOT EXISTS checkins_cs ON checkins (cs);

-- Photos of chargers, published only after moderation.
CREATE TABLE IF NOT EXISTS photos (
  id TEXT PRIMARY KEY,           -- 32 hex chars, random
  st TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending | ok | no
  at INTEGER NOT NULL,
  cap TEXT,
  w INTEGER, h INTEGER,
  mime TEXT NOT NULL,
  img BLOB NOT NULL,             -- max ~900 KB, re-encoded in the browser (no EXIF)
  th BLOB,                       -- thumbnail max ~80 KB
  ip TEXT,
  rep INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS photos_st ON photos (st, status);
CREATE INDEX IF NOT EXISTS photos_status ON photos (status);

-- Requests from companies and networks ("Da li je ovo vaša firma?") and corrections from readers.
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,            -- firma | mreza | ispravka | stanica
  slug TEXT,
  data TEXT NOT NULL,            -- JSON of the form
  email TEXT,
  at INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'new', -- new | done | rejected
  ip TEXT
);
CREATE INDEX IF NOT EXISTS requests_status ON requests (status);

-- Rate limits per key per day.
CREATE TABLE IF NOT EXISTS rl (
  k TEXT NOT NULL,
  day TEXT NOT NULL,
  n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (k, day)
);
