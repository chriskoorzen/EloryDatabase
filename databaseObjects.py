"""
Represent objects from database. No CRUD operations affecting the database may take place within these classes
"""


class DatabaseObject:
    """Abstract class for objects retrieved from database"""

    def __init__(self, db_ID: int, name: str):
        self.db_id = db_ID        # Primary key of object within database
        self.name = name


class TagGroup(DatabaseObject):

    def __init__(self,  db_ID: int, name: str, tags: list):
        super().__init__(db_ID, name)
        self.tags = tags


class Tag(DatabaseObject):

    def __init__(self,  db_ID: int, name: str, group: TagGroup):
        super().__init__(db_ID, name)
        self.group = group


class File(DatabaseObject):

    def __init__(self,  db_ID: int, name: str, path: str, tags: list):
        super().__init__(db_ID, name)
        self.path = path
        self.tags = tags

    @staticmethod
    def digest(file):
        """Return a unique hash code of a given file.

        The return must be unique to the file itself, should be platform-agnostic and resilient to meta-data changes.
        The goal is to identify a particular file (defined as a series of bits) regardless of its OS, underlying fs,
        or system architecture.
        """
        pass

