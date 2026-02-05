CREATE TABLE IF NOT EXISTS Files (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL UNIQUE,
    previewpath TEXT NOT NULL,
    description TEXT
);


CREATE TABLE IF NOT EXISTS Tags(
    id INTEGER PRIMARY KEY,
    tagname TEXT NOT NULL UNIQUE
);


CREATE TABLE IF NOT EXISTS Files_tags(
    file_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (file_id, tag_id),
    FOREIGN KEY (file_id) REFERENCES Files(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES Tags(id) ON DELETE CASCADE
);
