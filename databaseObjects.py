"""
Represent objects from database. No CRUD operations affecting the database may take place within these classes
"""
import hashlib
from os.path import basename, isfile
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

    def __init__(self,  db_id: int, name: str, tags=[]):
        super().__init__(db_id)
        self.name = name
        self.tags = set()
        for i in tags:
            self.tags.add(i)

    def __repr__(self):
        final = f"<{self.__class__} : {self.name} : id {self.db_id}>"
        return final


class Tag(DatabaseObject):

    def __init__(self,  db_id: int, name: str, group: TagGroup, files=[]):
        super().__init__(db_id)
        self.name = name
        self.group = group
        self.files = set()
        for i in files:
            self.files.add(i)

    def __repr__(self):
        final = f"{self.__class__} : {self.name} : id {self.db_id} : files {self.files}"
        return final


class File(DatabaseObject):

    def __init__(self,  db_id: int, path: str, hash_id: str, tags=[]):
        super().__init__(db_id)
        self.path = path
        self.name = basename(self.path)
        self.hash_id = hash_id
        self.tags = set()
        for i in tags:
            self.tags.add(i)

    def get_groups(self):
        for tag in self.tags:
            pass

    def __repr__(self):
        final = f"<{self.__class__} : {self.hash_id} : id {self.db_id}>"
        return final
