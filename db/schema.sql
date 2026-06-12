CREATE TABLE articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT NOT NULL UNIQUE,
    url_hash        TEXT NOT NULL UNIQUE,
    content_hash    TEXT NOT NULL,
    title           TEXT,
    author          TEXT,
    date            TEXT,
    source          TEXT NOT NULL,
    categories      TEXT,           -- JSON array
    tags            TEXT,           -- JSON array
    raw_text        TEXT,
    clean_text      TEXT,
    parse_status    TEXT DEFAULT 'pending',  -- pending | parsed | parse_error
    crawled_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    parsed_at       DATETIME,
    groq_summary    TEXT,
    report_id       INTEGER
);

CREATE INDEX idx_url_hash      ON articles(url_hash);
CREATE INDEX idx_content_hash  ON articles(content_hash);
CREATE INDEX idx_source        ON articles(source);
CREATE INDEX idx_parse_status  ON articles(parse_status);
CREATE INDEX idx_crawled_at    ON articles(crawled_at);

CREATE TABLE reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT,
    template    TEXT,
    content     TEXT,
    pdf_path    TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
