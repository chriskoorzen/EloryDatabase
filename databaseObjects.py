"""
Represent objects from database. No CRUD operations affecting the database may take place within these classes
"""
import hashlib
import os.path
import logging


class DatabaseObject:
    """Abstract class for objects retrieved from database"""

    def __init__(self, db_id: int):
        self.db_id = db_id        # Primary key of object within database
        
    def __eq__(self, other):
        if other == (self.__class__, self.db_id):
            return True
        return False

    def __hash__(self):
        return hash((self.__class__, self.db_id))


class TagGroup(DatabaseObject):

    def __init__(self,  db_id: int, name: str):
        super().__init__(db_id)
        self.name = name
        self.tags = dict()

    def __repr__(self):
        final = f"<{self.__class__} : {self.name} : id {self.db_id} : tags {self.tags.keys()}>"
        return final


class Tag(DatabaseObject):

    def __init__(self,  db_id: int, name: str, group: TagGroup):
        super().__init__(db_id)
        self.name = name
        self.group = group
        self.files = dict()

    def __repr__(self):
        final = f"<{self.__class__} : {self.name} : id {self.db_id} : files {self.files.keys()}>"
        return final


class File(DatabaseObject):

    def __init__(self,  db_id: int, path: str, hash_id: str):
        super().__init__(db_id)
        self.path = path
        self.hash_id = hash_id
        self.tags = dict()

    def __repr__(self):
        final = f"<{self.__class__} : {self.hash_id} : id {self.db_id} : files {self.tags.keys()}>"
        return final

    @staticmethod
    def digest(file):
        """Return a unique hash code of a given file.

        The return must be unique to the file itself, should be platform-agnostic and resilient to meta-data changes.
        The goal is to identify a particular file (defined as a series of bits) regardless of the OS, underlying fs,
        or system architecture.
        """
        if not os.path.isfile(file):
            logging.warning(f"{file} is not a valid file")
            return
        h = hashlib.md5()
        b = bytearray(128*1024)
        mv = memoryview(b)      # using memoryview, we can slice a buffer without copying it

        with open(file, 'rb', buffering=0) as file_obj:
            while n := file_obj.readinto(mv):
                h.update(mv[:n])
        return h.hexdigest()
