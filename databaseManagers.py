import logging
import sqlite3
import os.path

from databaseObjects import TagGroup, Tag, File
from SQLTemplates import tableTemplate, tables

# TODO decide on error policy and propagation


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
        if not os.path.isfile(path):
            logging.warning(f"File '{path}' does not exist.")
            return
        full_path = os.path.abspath(path)
        file_hash = File.digest(path)

        Database.CURSOR.execute(f"INSERT INTO files (file_path, file_hash_name) VALUES ('{full_path}', '{file_hash}')")
        Database.CONNECTION.commit()
        FileManager.files[Database.CURSOR.lastrowid] = File(Database.CURSOR.lastrowid, full_path, file_hash)
        logging.info(f"Added file '{full_path}' to database")

    @staticmethod
    def remove_file(file_id):
        # TODO Should be able to delete files even if tagged.
        f = FileManager.files[file_id]
        Database.CURSOR.execute(f"DELETE FROM files WHERE file_id={f.db_id}")       # This SQL should cascade auto
        # Database.CURSOR.execute(f"DELETE FROM tagged_files_m2m WHERE file={f.db_id}")     # Fall back if cascade fails
        Database.CONNECTION.commit()
        for tag in f.tags.values():
            # purge from tags
            del tag.files[file_id]
        logging.info(f"Removed file '{f.path}' from database")
        del f

    @staticmethod
    def add_tag_to_file(file_id, tag: Tag):
        f = FileManager.files[file_id]
        Database.CURSOR.execute(f"INSERT INTO tagged_files_m2m (tag, file) VALUES ({tag.db_id}, {f.db_id})")
        Database.CONNECTION.commit()
        f.tags[tag.db_id] = tag
        tag.files[f.db_id] = f
        logging.info(f"Tagged file '{f.path}' with tag '{tag.name}'")

    @staticmethod
    def remove_tag_from_file(file_id, tag: Tag):
        f = FileManager.files[file_id]
        Database.CURSOR.execute(f"DELETE FROM tagged_files_m2m WHERE tag={tag.db_id} AND file={f.db_id}")
        Database.CONNECTION.commit()
        logging.info(f"Untagged file '{f.path}' from tag '{tag.name}'")
        del f.tags[tag.db_id]
        del tag.files[file_id]

    # TODO Utility function to integrity check file_path, while keeping file_hash consistent ->


class TagManager:

    tags = dict()
    groups = dict()

    @staticmethod
    def _load_members():
        # Get tag groups
        Database.CURSOR.execute("SELECT group_id, group_name FROM tag_groups")
        result = Database.CURSOR.fetchall()
        for item in result:
            TagManager.groups[item[0]] = TagGroup(item[0], item[1])
        logging.info(f"{len(TagManager.groups)} Tag groups loaded...")

        # Get tags
        for group_id in TagManager.groups.keys():
            Database.CURSOR.execute(f"SELECT tag_id, tag_name FROM tags WHERE tag_group={group_id}")
            result = Database.CURSOR.fetchall()
            for tag_attr in result:
                tag = Tag(tag_attr[0], tag_attr[1], TagManager.groups[group_id])
                TagManager.tags[tag.db_id] = tag
                TagManager.groups[group_id].tags[tag.db_id] = tag
        logging.info(f"{len(TagManager.tags)} Tags loaded...")

    @staticmethod
    def _load_file_data():
        # Only call when Tags and TagGroups have been instantiated
        for tag_id in TagManager.tags.keys():
            Database.CURSOR.execute(f"SELECT file FROM tagged_files_m2m WHERE tag={tag_id}")
            result = Database.CURSOR.fetchall()
            for file_id in result:
                file_id = file_id[0]
                TagManager.tags[tag_id].files[file_id] = FileManager.files[file_id]

    @staticmethod
    def new_group(name):
        Database.CURSOR.execute(f'INSERT INTO tag_groups (group_name) VALUES ("{name}")')
        Database.CONNECTION.commit()
        obj_id = Database.CURSOR.lastrowid
        TagManager.groups[obj_id] = (TagGroup(obj_id, name))
        logging.info(f"New group '{name}' added to database")

    @staticmethod
    def delete_group(group_id):
        g = TagManager.groups.pop(group_id)
        Database.CURSOR.execute(f'DELETE FROM tag_groups WHERE group_id={g.db_id}')
        Database.CONNECTION.commit()
        logging.info(f"Group '{g.name}' removed from database")
        del g

    @staticmethod
    def rename_group(group_id, new_name):
        g = TagManager.groups[group_id]
        Database.CURSOR.execute(f'UPDATE tag_groups SET group_name="{new_name}" WHERE group_id={g.db_id}')
        Database.CONNECTION.commit()
        logging.info(f"Group '{g.name}' renamed to '{new_name}'")
        g.name = new_name

    @staticmethod
    def new_tag(name: str, group: TagGroup):
        Database.CURSOR.execute(f'INSERT INTO tags (tag_name, tag_group) VALUES ("{name}", {group.db_id})')
        Database.CONNECTION.commit()
        tag = Tag(Database.CURSOR.lastrowid, name, group)
        TagManager.tags[tag.db_id] = tag
        group.tags[tag.db_id] = tag
        logging.info(f"New tag '{tag}' added to database")

    @staticmethod
    def delete_tag(tag_id):
        # Must not be able to delete tags attached to files
        t = TagManager.tags.pop(tag_id)
        Database.CURSOR.execute(f'DELETE FROM tags WHERE tag_id={t.db_id} AND tag_group={t.group.db_id}')
        Database.CONNECTION.commit()
        t.group.tags.pop(t.db_id)
        logging.info(f"Tag '{t}' removed from database")
        del t

    @staticmethod
    def rename_tag(tag_id, new_name: str):
        t = TagManager.tags[tag_id]
        Database.CURSOR.execute(f'UPDATE tags SET tag_name="{new_name}" WHERE tag_id={t.db_id}')
        Database.CONNECTION.commit()
        logging.info(f"Tag '{t.name}' renamed to '{new_name}'")
        t.name = new_name


class Database:

    NAME = ''
    CONNECTION = ''
    CURSOR = ''

    FileManager = FileManager
    TagManager = TagManager

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

        # Load tag groups, tags, files and their respective connections
        Database.TagManager._load_members()
        Database.FileManager._load_members()
        Database.TagManager._load_file_data()
        Database.FileManager._load_tag_data()

        # Database program ready
        logging.info(f"Database '{path}' ready for operation.")

    @staticmethod
    def _create_db():
        Database.CURSOR.executescript(tableTemplate)

    @staticmethod
    def close_db():
        logging.info(f"Getting ready to close database '{Database.NAME}' ...")
        TagManager.tags.clear()
        TagManager.groups.clear()
        FileManager.files.clear()
        logging.info(f"Objects cleared from memory ...")
        Database.CONNECTION.close()
        logging.info(f"Database '{Database.NAME}' closed and ready for new connection.")
