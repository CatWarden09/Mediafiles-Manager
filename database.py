import os, sqlite3, config

class DatabaseHandler:
    def __init__(self):

        folder_path = os.path.join(config.assign_script_dir(), "fhandler_data")
        os.makedirs(folder_path, exist_ok=True)
        self.db_path = os.path.join(folder_path, "files.db")

        self.connect_to_database()

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Files (
        id INTEGER PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL UNIQUE,
        previewpath TEXT NOT NULL,
        description TEXT
        )              
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Tags(
        id INTEGER PRIMARY KEY,
        tagname TEXT NOT NULL UNIQUE)
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Files_tags(
        file_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (file_id, tag_id),
        FOREIGN KEY (file_id) REFERENCES Files(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES Tags(id) ON DELETE CASCADE
        )
        """
        )

        self.cursor.execute(
            """INSERT OR IGNORE INTO Tags(tagname) VALUES
            ("Audio"),
            ("Video"),
            ("Image")
            """
        )

        self.save_changes()

    def connect_to_database(self):

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

        # need to activate foreign_keys on every DB connection
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def save_changes(self):
        self.connection.commit()

    def close_connection(self):
        self.connection.close()

    def save_to_database(self, file_name: str, file_path: str, preview_path: str):
        self.cursor.execute(
            "INSERT INTO Files (filename, filepath, previewpath) VALUES (?, ?, ?)",
            (file_name, file_path, preview_path),
        )

    def save_tag_to_database(self, tag_name: str):
        self.cursor.execute(
            "INSERT INTO Tags (tagname) VALUES (?)",
            (tag_name,),
        )
        self.save_changes()

    def delete_tag_from_database(self, tag_hame: str):
        self.cursor.execute("DELETE FROM Tags WHERE tagname = ?", (tag_hame,))
        self.save_changes()

    def get_all_tagnames(self):
        self.cursor.execute("SELECT tagname FROM Tags")
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    # Get all tag names assigned to a file:
    # 1. Start from Tags table
    # 2. Join Files_tags to find tag-file links
    # 3. Join Files to know which file each tag belongs to
    # 4. Filter by file name
    def get_current_item_tags(self, item):
        self.cursor.execute(
            """
            SELECT t.tagname
            FROM Tags t
            
            JOIN Files_tags ft on ft.tag_id = t.id
            JOIN Files f ON ft.file_id = f.id
            WHERE f.filename = ?

        """,
            (item,),
        )
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def save_current_item_tags(self, item, tags_list):
        for tag in tags_list:
            self.cursor.execute(
                """INSERT OR IGNORE INTO Files_tags (file_id, tag_id)
                SELECT f.id, t.id
                FROM Files f
                JOIN Tags t ON t.tagname = ?
                WHERE f.filename = ?
                
                """,
                (tag, item),
            )
        self.save_changes()

    # check if the tag is already in the table and return True if the DB query returns !=Null, return False otherwise
    def tag_exists(self, tag_name: str) -> bool:
        self.cursor.execute("SELECT 1 FROM Tags WHERE tagname = ?", (tag_name,))
        return self.cursor.fetchone() is not None

    def get_previewpath_by_filename(self, file):
        self.cursor.execute("SELECT previewpath FROM Files WHERE filename = ?", (file,))
        row = self.cursor.fetchone()
        return row[0]
    
    def get_previewpath_by_filepath(self, filepath):
        self.cursor.execute("SELECT previewpath FROM Files WHERE filepath = ?", (filepath,))
        row = self.cursor.fetchone()
        return row[0]

    def get_all_filenames(self):
        self.cursor.execute("SELECT filename FROM Files")
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]
    
    def get_files_by_filepath(self, filepath):
        self.cursor.execute(
            "SELECT filename, filepath FROM Files WHERE filepath LIKE ?",
            (filepath + '%',)
        )
        rows = self.cursor.fetchall()
        files_in_folder = [
            filename for filename, fullpath in rows
            if os.path.dirname(fullpath) == filepath.rstrip(os.sep)
        ]
        return files_in_folder

    def get_filepath(self, file):
        self.cursor.execute("SELECT filepath FROM Files WHERE filename = ?", (file,))
        row = self.cursor.fetchone()
        return row[0]

    def get_all_filepaths(self):
        self.cursor.execute("SELECT filepath FROM Files")
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def get_files_by_tags(self, tags_list):
        if not tags_list:
            return []
        placeholders = ", ".join(["?"] * len(tags_list))
        query = f"""
            SELECT f.filename
            FROM Files f
            JOIN Files_tags ft on ft.file_id = f.id
            JOIN Tags t ON ft.tag_id = t.id
            WHERE t.tagname IN ({placeholders})
            GROUP BY f.id
            HAVING COUNT(DISTINCT t.tagname) = ?
        """
        params = tags_list + [len(tags_list)]
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def get_files_by_text(self, description):
        query = "SELECT filename FROM Files WHERE description LIKE ? OR filename LIKE ?"
        self.cursor.execute(query, (f"%{description}%", f"%{description}%"))
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def update_file_description(self, file, description: str):
        self.cursor.execute(
            "UPDATE Files SET description = ? WHERE filename = ?", (description, file)
        )
        self.save_changes()

    def get_file_description(self, file):
        self.cursor.execute("SELECT description FROM Files WHERE filename = ?", (file,))
        row = self.cursor.fetchone()
        return row[0]

    # Delete all tag-file pairs where ids of tags and files are equal to the method arguments
    def delete_current_item_tags(self, item, tags_list):
        for tag in tags_list:
            self.cursor.execute(
                """
                DELETE FROM Files_tags
                WHERE file_id = (SELECT id FROM Files WHERE filename = ?)
                AND tag_id = (SELECT id FROM Tags WHERE tagname = ?)

                """,
                (item, tag),
            )
        self.save_changes()

    def delete_file_by_filepath(self, filepath):
        self.cursor.execute("DELETE FROM Files WHERE filepath = ?", (filepath,))
