"""
Represent objects from database. No CRUD operations affecting the database may take place within these classes
"""
from os.path import basename, isfile
from operator import itemgetter

import logging
object_logger = logging.getLogger(__name__)
object_logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(fmt)
object_logger.addHandler(handler)
object_logger.propagate = False


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
        self.tags = {}

    @classmethod
    def load_tag_collection(cls, database):
        g_entries, t_entries = database.read_entry([("tag_groups", "all"), ("tags", "all")])
        groups = {}
        tags = {}
        g_entries.sort()
        t_entries.sort(key=itemgetter(2), reverse=True)
        for g in g_entries:
            new_g = cls(g[0], g[1])
            groups[g[1]] = new_g          # store group items by name
            while t_entries and t_entries[-1][2] == g[0]:
                t = t_entries.pop()
                new_t = Tag(t[0], t[1], new_g)
                new_g.tags[t[0]] = new_t
                tags[t[0]] = new_t
        object_logger.info("Group and Tag objects initialized")
        return groups, tags

    # TODO this can be optimized with a memoization-like technique
    def has_files(self):
        for tag in self.tags.values():
            if tag.files:
                return True
        return False

    @classmethod
    def new_group(cls, database, name):
        # Only sending one entry, so only expect a single return tuple
        group_id = database.create_entry("group", [{"group_name": name}])[0]
        if not group_id[0]:
            object_logger.warning("Object creation failed: " + str(group_id[1]))
            return group_id
        object_logger.info(f"Created new group object '{name}'")
        return True, cls(group_id[1], name)

    def delete(self, database):
        success = database.delete_entry("group", [{"group_id": self.db_id}])[0]
        if not success[0]:
            object_logger.warning("Group object deletion failed: " + str(success[1]))
            return False
        object_logger.info(f"Deleted group object '{self.name}'")
        return True

    def create_tag(self, database, tag_name):
        # Only sending one entry, so only expect a single return tuple
        tag_id = database.create_entry("tag", [{'tag_name': tag_name, 'group': self.db_id}])[0]
        if not tag_id[0]:
            object_logger.warning("Object creation failed: " + str(tag_id[1]))
            return tag_id
        new_tag = Tag(tag_id[1], tag_name, self)
        self.tags[tag_id[1]] = new_tag
        object_logger.info(f"Created new tag object '{tag_name}'")
        return True, new_tag

    def delete_tag(self, database, tag):
        if tag.db_id not in self.tags:
            object_logger.critical(f"Tag '{tag.name}' does not belong to group '{self.name}' ")
            return False
        if tag.files:
            object_logger.warning("Cannot delete a tag with files")
            return False
        success = database.delete_entry("tag", [{"tag_id": tag.db_id}])[0]
        if not success[0]:
            object_logger.warning("Tag object deletion failed: " + str(success[1]))
            return False
        del self.tags[tag.db_id]
        object_logger.info(f"Deleted tag object '{tag.name}'")
        return True

    def __repr__(self):
        return f"<{self.__class__} : {self.name} : id {self.db_id}>"


class Tag(DatabaseObject):

    def __init__(self,  db_id: int, name: str, group: TagGroup):
        super().__init__(db_id)
        self.name = name
        self.group = group
        self.files = {}

    def __repr__(self):
        return f"{self.__class__} : {self.name} : id {self.db_id} : files {self.files}"


class File(DatabaseObject):

    def __init__(self,  db_id: int, path: str, hash_id: str):
        super().__init__(db_id)
        self.path = path
        self.name = basename(self.path)
        self.hash_id = hash_id
        self.tags = {}

    @classmethod
    def load_files(cls, database, tag_dict):
        f_entries = database.read_entry([("files", "all")])[0]
        files = {}
        for f in f_entries:
            new_f = cls(f[0], f[1], f[2])
            files[f[1]] = new_f         # Store by path string
            for t in f[3]:              # Loop through tag ids
                tag_obj = tag_dict[t]
                tag_obj.files[f[1]] = new_f     # reference files by path
                new_f.tags[tag_obj.db_id] = tag_obj
        object_logger.info("File objects initialized")
        return files

    @classmethod
    def new_file(cls, path, database):
        file = database.create_entry("file", [{'file_path': path}])[0]  # Expect a list with 1 tuple
        if not file[0]:
            object_logger.warning("Object creation failed: " + str(file[1]))
            # Check why:
            file_hash = file[2]
            check = database.read_entry([("files", "file_hash_name", file_hash)])[0]
            if not len(check):  # This empty
                return False, f"The file at '{path}' exists but is not recognized. " \
                              f"Have you edited this file or renamed a different file to this name " \
                              f"since last adding it to the database?"
            path = check[0][1]
            return False, f"This file is a duplicate of '{path}' that has already been added to the database."
        object_logger.info(f"New File object '{file[0]}' created")
        return True, cls(file[0], path, file[1])

    def delete(self, database):
        success = database.delete_entry("file", [{'file_id': self.db_id}])[0]       # Expect a return value?
        if not success[0]:
            object_logger.warning("File object deletion failed: " + str(success[1]))
            return False
        object_logger.info(f"Deleted File object '{self.db_id}'")
        return True

    def add_tags(self, database, *tags):
        result = []
        pairs = database.create_entry("tag-file", [{'file_id': self.db_id, 'tag_id': tag.db_id} for tag in tags])
        for i in range(len(tags)):
            if pairs[i][0]:
                self.tags[tags[i].db_id] = tags[i]
                tags[i].files[self.path] = self
                result.append((True, pairs[i][0]))
                object_logger.info(f"File object '{self.db_id}' new tag '{tags[i].db_id}' linked")
                continue
            object_logger.warning("Object creation failed: " + str(pairs[i][1]))
            result.append(pairs[i])     # (False, errmsg)
        return result

    def remove_tags(self, database, *tags):
        # TODO since this is a compound operation, some might fail and others succeed
        status = database.delete_entry("tag-file", [{'file_id': self.db_id, 'tag_id': tag.db_id} for tag in tags])
        for tag in range(len(tags)):
            if status[tag][0]:
                del self.tags[tags[tag].db_id]
                del tags[tag].files[self.path]
                object_logger.info(f"File object '{self.db_id}' unlinked from tag '{tags[tag].db_id}' ")
            else:
                object_logger.warning(f"Failed to unlink file object '{self.db_id}' from tag '{tags[tag].db_id}' ")
        return True

    def get_groups(self):
        groups = set()
        for tag in self.tags.values():
            groups.add(tag.group)
        return groups

    def __repr__(self):
        return f"<{self.__class__} : {self.hash_id} : id {self.db_id}>"
