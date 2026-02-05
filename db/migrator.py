import config, os, sqlite3



class DatabaseMigrator:
    def __init__(self, connection, error_window):
        self.connection = connection
        self.error_window = error_window
        self.cursor = self.connection.cursor()

        self.create_migrations_table()

    def create_migrations_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Migrations(
            id TEXT PRIMARY KEY)
            """
        )
        self.connection.commit()

    def get_applied_migrations(self):
        self.cursor.execute(
            "SELECT id FROM Migrations"
        )
        rows = self.cursor.fetchall()

        return [row[0] for row in rows]
    

    def apply_migrations(self):
        applied_migrations = self.get_applied_migrations()
        migrations_path = os.path.join(config.assign_script_dir(), "db", "migrations")

        for migration in sorted(os.listdir(migrations_path)):
            if migration in applied_migrations:
                continue
            
            migration_path = os.path.join(migrations_path, migration)
            with open(migration_path, "r", encoding="utf-8") as m:
                query = m.read()

            try:
                with self.connection:
                    self.connection.executescript(query)
                    self.cursor.execute("INSERT INTO Migrations (id) VALUES (?)", (migration,))
            except sqlite3.OperationalError as e:
                self.error_window.show_error_message("Произошла ошибка миграции:" + "\n" + str(e))
                



