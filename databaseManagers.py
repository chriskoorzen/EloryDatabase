import logging
import sqlite3
import os.path

from SQLTemplates import tableTemplate, tables


class FileManager:

    @staticmethod
    def addFile(path):
        pass

    @staticmethod
    def removeFile(path):
        pass

    @staticmethod
    def addFileTag(file, tag):
        pass

    @staticmethod
    def removeFileTag(file, tag):
        pass

    @staticmethod
    def getFilesfromTags(*tags):
        print(f"{len(tags)} tags specified")
        print("retrieve files")
        pass


class TagManager:

    tags = []
    groups = []

    @staticmethod
    def newGroup(name):
        pass

    @staticmethod
    def deleteGroup(name):
        pass

    @staticmethod
    def renameGroup(name, new_name):
        pass

    @staticmethod
    def newTag(name):
        pass

    @staticmethod
    def deleteTag(name):
        pass

    @staticmethod
    def renameTag(name, new_name):
        pass


class Database:

    NAME = ''
    CONNECTION = ''
    CURSOR = ''

    FileManager = FileManager
    TagManager = TagManager

    @staticmethod
    def connectDB(path):

        if not os.path.isfile(path):
            logging.warning(f"File does not exist. Creating new sqlite3 database at '{path}'")

        # TODO differentiate between db name and absolute path - use set variables instead of supplied "path variable"
        Database.NAME = path
        Database.CONNECTION = sqlite3.connect(Database.NAME)
        Database.CURSOR = Database.CONNECTION.cursor()

        # Check if database is valid -> if so, is it empty?
        try:
            Database.CURSOR.execute("PRAGMA schema_version")
            logging.info(f"Connected to database '{path}'")
        except sqlite3.DatabaseError:
            logging.critical(f"'{path}' is not a valid sqlite3 database. Abort operation.")
            return
        if Database.CURSOR.fetchone()[0] == 0:
            # Database is valid but empty -> setup tables
            logging.info(f"Database '{path}' is empty...")
            Database._createDB()
            Database.CONNECTION.commit()
            logging.info(f"Tables created for database '{path}'")

        # Check if needed tables are present
        Database.CURSOR.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        db_tables = {x[0] for x in Database.CURSOR.fetchall()}
        fmt_tables = {x for x in tables.keys()}
        if not fmt_tables <= db_tables:             # if format tables is not present in (subset of) database...
            logging.critical(f"Required tables not present in database '{path}'. Abort operation.")
            return
        # Check for column format mismatch
        for i in fmt_tables:
            Database.CURSOR.execute(f"PRAGMA table_info({i});")
            columns = {x[1] for x in Database.CURSOR.fetchall()}
            expected = {x for x in tables[i].keys() if 'FOREIGN' not in x and 'UNIQUE' not in x}    # TODO find better way to filter
            if not columns == expected:
                logging.critical(f"Tables do not match required column formats in database '{path}'. Abort operation.")
                return
        logging.info(f"Table formats recognized in database '{path}'")

        # Warn if foreign tables are present
        if len(db_tables) > len(fmt_tables):
            logging.warning(f"Additional unrecognized tables detected in database '{path}'")

        # Necessary settings for database
        Database.CURSOR.execute("PRAGMA foreign_keys = ON")  # Enforce Foreign Key constraints
        Database.CONNECTION.commit()
        logging.info(f"Database '{path}' ready for operation.")

    @staticmethod
    def _createDB():
        # try:
        Database.CURSOR.executescript(tableTemplate)
        # print("Tables successfully created")
        # except sqlite3.OperationalError:
        #     print("One or more tables with the same name already exists.\nOperation Aborted.")
        pass

