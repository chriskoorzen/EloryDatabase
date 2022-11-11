"""
Represent objects from database. Let objects take care of CRUD operations affecting the database.
"""
import hashlib
import os.path
import logging
import sqlite3

from SQLTemplates import tableTemplate, tables

# TODO let objects modify themselves in database? (will lead to more inter-dependent code)
# TODO Create Retrieve Update Delete (CRUD) functions


class DatabaseObject:
    """Abstract class for objects retrieved from database"""
    TEST_VARIABLE = ''

    def __init__(self, db_id):
        self.db_id = db_id

    def __eq__(self, other):
        if other == (self.__class__, self.db_id):
            return True
        return False

    def __hash__(self):
        return hash((self.__class__, self.db_id))


class TagGroup(DatabaseObject):

    TABLE_FORMAT = {"tag_groups": {"group_id": "INTEGER PRIMARY KEY", "group_name": "TEXT UNIQUE NOT NULL"}}
    ALTERNATIVE = {"table_name": "tag_groups",
                   "columns": {"group_id": "INTEGER PRIMARY KEY",
                               "group_name": "TEXT UNIQUE NOT NULL"},
                   "constraints": {},
                   }

    def __init__(self, name: str, db_id: int = None):
        self.name = name
        self.tags = set()
        if db_id is None:
            # No row_id supplied, so this must be a new object. i.e. It is not retrieved
            Database.CURSOR.execute(f'INSERT INTO tag_groups (group_name) VALUES ("{self.name}")')
            Database.CONNECTION.commit()
            super().__init__(Database.CURSOR.lastrowid)
            logging.info(f"New group '{self.name}' added to database")
        else:
            super().__init__(db_id)

    def __repr__(self):
        return self.name

    def add_tag(self, tag):
        self.tags.add(tag)

    def delete_from_db(self):
        # TODO must inhibit delete where tags still reference Group
        Database.CURSOR.execute(f'DELETE FROM tag_groups WHERE group_id={self.db_id}')
        Database.CONNECTION.commit()
        logging.info(f"Group '{self.name}' removed from database")
        return Database.CURSOR.rowcount     # 0 on failure, 1 on success. if 0 > return > 1, is bug

    def update_name(self, new_name):
        Database.CURSOR.execute(f'UPDATE tag_groups SET group_name="{new_name}" WHERE group_id={self.db_id}')
        Database.CONNECTION.commit()
        logging.info(f"Group '{self.name}' renamed to '{new_name}'")
        self.name = new_name
        return Database.CURSOR.rowcount     # 0 on failure, 1 on success. if 0 > return > 1, is bug

    @classmethod
    def retrieve_all(cls):
        Database.CURSOR.execute("SELECT group_id, group_name FROM tag_groups")
        result = Database.CURSOR.fetchall()
        all_groups = []
        for item in result:
            all_groups.append(cls(item[1], item[0]))
        logging.info(f"{len(all_groups)} Tag Groups loaded...")
        return all_groups


class Tag(DatabaseObject):

    def __init__(self,  db_id: int, name: str, group: TagGroup):
        super().__init__(db_id)
        self.name = name
        self.group = group

    def __repr__(self):
        return f"{self.group} : {self.name}"


class File(DatabaseObject):

    def __init__(self,  db_id: int, name: str, path: str, tags: list = []):
        super().__init__(db_id, name)
        self.path = path
        self.tags = tags

    def __repr__(self):
        return self.path

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


class TagManager:

    tags = []
    groups = []

    @classmethod
    def _load_members(cls):
        # Get tag groups
        for i in TagGroup.retrieve_all():
            cls.groups.append(i)

        # Get tags
        for item in TagManager.groups:
            Database.CURSOR.execute(f"SELECT tag_id, tag_name FROM tags WHERE tag_group={item.db_id}")
            result = Database.CURSOR.fetchall()
            for tag in result:
                TagManager.tags.append(Tag(tag[0], tag[1], item))
        logging.info(f"{len(TagManager.tags)} Tags loaded...")

    @classmethod
    def new_group(cls, name):
        cls.groups.append(TagGroup(name))

    @classmethod
    def delete_group(cls, group: TagGroup):
        group.delete_from_db()
        cls.groups.remove(group)

    @staticmethod
    def new_tag(name: str, group: TagGroup):
        Database.CURSOR.execute(f'INSERT INTO tags (tag_name, tag_group) VALUES ("{name}", {group.db_id})')
        Database.CONNECTION.commit()
        obj_id = Database.CURSOR.lastrowid
        new_tag = Tag(obj_id, name, group)
        TagManager.tags.append(new_tag)
        group.tags.append(new_tag)
        logging.info(f"New tag '{new_tag}' added to database")

    @staticmethod
    def delete_tag(name: str, group: TagGroup):
        Database.CURSOR.execute(f'DELETE FROM tags WHERE tag_name="{name}" AND tag_group={group.db_id}')
        Database.CONNECTION.commit()
        tag = f"{group.name} : {name}"
        TagManager.tags.remove(tag)
        group.tags.remove(tag)
        logging.info(f"Tag '{tag}' removed from database")

    @staticmethod
    def rename_tag(name: str, group: TagGroup, new_name: str):
        Database.CURSOR.execute(f'UPDATE tags SET tag_name="{new_name}" WHERE tag_name="{name}" AND tag_group={group.db_id}')
        Database.CONNECTION.commit()
        tag = f"{group.name} : {name}"
        ndx = TagManager.tags.index(tag)
        TagManager.tags[ndx].name = new_name
        logging.info(f"Tag '{name}' renamed to '{new_name}'")


class FileManager:

    files = dict()

    @staticmethod
    def _load_members():
        # Get tag groups
        Database.CURSOR.execute("SELECT file_id, file_path, file_hash_name FROM files")
        result = Database.CURSOR.fetchall()
        for item in result:
            FileManager.files[item[0]] = File(item[0], item[1], item[2])
        logging.info(f"{len(FileManager.files)} Files loaded...")

    @staticmethod
    def _load_tag_data():
        # Only call when Tags and TagGroups have been instantiated
        for file_id in FileManager.files.keys():
            Database.CURSOR.execute(f"SELECT tag FROM tagged_files_m2m WHERE file={file_id}")
            result = Database.CURSOR.fetchall()
            for tag_id in result:
                tag_id = tag_id[0]
                FileManager.files[file_id].tags[tag_id] = TagManager.tags[tag_id]

    @staticmethod
    def add_file(path):
        # TODO handle multiple files -> RETURN row_ids?
        if not os.path.isfile(path):
            logging.warning(f"File '{path}' does not exist.")
            return
        full_path = os.path.abspath(path)
        file_hash = File.digest(path)
        Database.CURSOR.execute(f"INSERT INTO files (file_path, file_hash_name) VALUES ('{full_path}', '{file_hash}')")
        Database.CONNECTION.commit()
        logging.info(f"Added file '{full_path}' to database")

    @staticmethod
    def remove_file(path):
        # TODO currently only accepts 'path' argument for file removal - poses problem when file path changes and ->
        # TODO -> a delete is desired. Currently it will fail and leave the row "stuck", until both path and id matches.
        if not os.path.isfile(path):
            logging.warning(f"File '{path}' does not exist.")
            return
        full_path = os.path.abspath(path)
        file_hash = File.digest(path)
        Database.CURSOR.execute(f"DELETE FROM files WHERE file_path='{full_path}' AND file_hash_name='{file_hash}'")
        if Database.CURSOR.rowcount == 0:
            # No actual remove took place
            logging.critical(f"Failed to remove file '{path}'. Abort.")
            return
        Database.CONNECTION.commit()
        logging.info(f"Removed file '{full_path}' from database")

    @staticmethod
    def add_file_tag(path, tag: Tag):
        # TODO accept multiple tags?
        # TODO only matches file if path and id is same (problem)
        if not os.path.isfile(path):
            logging.warning(f"File '{path}' does not exist.")
            return
        full_path = os.path.abspath(path)
        file_hash = File.digest(path)
        Database.CURSOR.execute(f"INSERT INTO tagged_files_m2m (tag, file) VALUES ({tag.db_id}, (SELECT file_id FROM files WHERE file_path='{full_path}' AND file_hash_name='{file_hash}'))")
        Database.CONNECTION.commit()
        logging.info(f"Tagged file '{path}' with tag '{tag}'")

    @staticmethod
    def remove_file_tag(path, tag):
        # TODO accept multiple tags?
        # TODO only matches file if path and id is same (problem)
        if not os.path.isfile(path):
            logging.warning(f"File '{path}' does not exist.")
            return
        full_path = os.path.abspath(path)
        file_hash = File.digest(path)
        Database.CURSOR.execute(f"DELETE FROM tagged_files_m2m WHERE tag={tag.db_id} AND file=(SELECT file_id FROM files WHERE file_path='{full_path}' AND file_hash_name='{file_hash}')")
        if Database.CURSOR.rowcount == 0:
            # No actual remove took place
            logging.critical(f"Failed to untag file '{path}' with tag '{tag}'. Abort.")
            return
        Database.CONNECTION.commit()

    @staticmethod
    def get_files_from_tag(tag: Tag):
        Database.CURSOR.execute(f"SELECT file_id, file_hash_name, file_path FROM files WHERE file_id IN (SELECT file FROM tagged_files_m2m WHERE tag={tag.db_id})")
        result = Database.CURSOR.fetchall()
        logging.info(f"Retrieved {len(result)} files for tag '{tag}'")
        return [File(x[0], x[1], x[2]) for x in result]

    # TODO add internal function for file verification and hashing, replacing duplicate code
    # TODO Utility function to integrity check file_path, while keeping file_hash consistent ->
    # TODO --> actually need better way to handle file identity and objects


class Database:

    NAME = ''
    CONNECTION = ''
    CURSOR = ''

    # FileManager = FileManager
    # TagManager = TagManager

    @staticmethod
    def connect_db(path):

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
            Database.CONNECTION.close()
            # raise sqlite3.DatabaseError       # TODO better to raise error instead? or let default error propagate?
            return
        if Database.CURSOR.fetchone()[0] == 0:
            # Database is valid but empty -> setup tables
            logging.info(f"Database '{path}' is empty...")
            Database._create_db()
            Database.CONNECTION.commit()
            logging.info(f"Tables created for database '{path}'")

        # Check if needed tables are present
        Database.CURSOR.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        db_tables = {x[0] for x in Database.CURSOR.fetchall()}
        fmt_tables = {x for x in tables.keys()}
        if not fmt_tables <= db_tables:             # if format tables is not present in (subset of) database...
            logging.critical(f"Required tables not present in database '{path}'. Abort operation.")
            Database.CONNECTION.close()
            return
        # Check for column format mismatch
        for i in fmt_tables:
            Database.CURSOR.execute(f"PRAGMA table_info({i});")
            columns = {x[1] for x in Database.CURSOR.fetchall()}
            # TODO find better way to filter -> the below method is fragile
            expected = {x for x in tables[i].keys() if 'FOREIGN' not in x and 'UNIQUE' not in x}
            if not columns == expected:
                logging.critical(f"Tables do not match required column formats in database '{path}'. Abort operation.")
                Database.CONNECTION.close()
                return
        logging.info(f"Table formats recognized in database '{path}'")

        # Warn if foreign tables are present
        if len(db_tables) > len(fmt_tables):
            logging.warning(f"Additional unrecognized tables detected in database '{path}'")

        # Necessary settings for database
        Database.CURSOR.execute("PRAGMA foreign_keys = ON")  # Enforce Foreign Key constraints
        Database.CONNECTION.commit()

        # TODO load tags, tag groups, (and file stats?)
        # Database.TagManager._load_members()

        # Database program ready
        logging.info(f"Database '{path}' ready for operation.")

    @staticmethod
    def _create_db():
        Database.CURSOR.executescript(tableTemplate)

    @staticmethod
    def close_db():
        # TODO close connection and purge objects from Managers (refresh and ready for new connection)
        pass
