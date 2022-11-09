import sqlite3
from SQLTemplates import tableTemplate


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
        Database.NAME = path
        # TODO see if file actually exists before creating new DB - warn user
        Database.CONNECTION = sqlite3.connect(Database.NAME)
        # TODO verify if db tables exists and matches format - raise error if unknown tables are present (pass over empty db)

        Database.CURSOR = Database.CONNECTION.cursor()
        Database.CURSOR.execute("PRAGMA foreign_keys = ON")  # Enforce Foreign Key constraints
        Database.CONNECTION.commit()

        # TODO  - if new and empty db, instantiate DB format

    @staticmethod
    def _createDB():
        # try:
        Database.CURSOR.executescript(tableTemplate)
        # print("Tables successfully created")
        # except sqlite3.OperationalError:
        #     print("One or more tables with the same name already exists.\nOperation Aborted.")
        pass

