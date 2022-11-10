import logging
import sqlite3
import os.path

from databaseObjects import TagGroup, Tag, File
from SQLTemplates import tableTemplate, tables


class FileManager:

    @staticmethod
    def addFile(path):
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
    def removeFile(path):
        # TODO currently only accepts 'path' argument for file removal - poses problem when file path changes and
        # TODO a delete is desired -> currently it will fail and leave the row "stuck", until both path and id matches.
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
    def addFileTag(path, tag: Tag):
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
    def removeFileTag(path, tag):
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
    def getFilesfromTag(tag: Tag):
        Database.CURSOR.execute(f"SELECT file_id, file_hash_name, file_path FROM files WHERE file_id IN (SELECT file FROM tagged_files_m2m WHERE tag={tag.db_id})")
        result = Database.CURSOR.fetchall()
        logging.info(f"Retrieved {len(result)} files for tag '{tag}'")
        return [File(x[0], x[1], x[2]) for x in result]

    # TODO add internal function for file verification and hashing
    # TODO Utility function to integrity check file_path, while keeping file_hash consistent


class TagManager:

    tags = []
    groups = []

    @staticmethod
    def _load_members():
        # Get tag groups
        Database.CURSOR.execute("SELECT group_id, group_name FROM tag_groups")
        result = Database.CURSOR.fetchall()
        for item in result:
            TagManager.groups.append(TagGroup(item[0], item[1]))
        logging.info(f"{len(TagManager.groups)} Tag groups loaded...")

        # Get tags
        for item in TagManager.groups:
            Database.CURSOR.execute(f"SELECT tag_id, tag_name FROM tags WHERE tag_group={item.db_id}")
            result = Database.CURSOR.fetchall()
            for tag in result:
                TagManager.tags.append(Tag(tag[0], tag[1], item))
        logging.info(f"{len(TagManager.tags)} Tags loaded...")

    @staticmethod
    def newGroup(name):
        Database.CURSOR.execute(f'INSERT INTO tag_groups (group_name) VALUES ("{name}")')
        Database.CONNECTION.commit()
        obj_id = Database.CURSOR.lastrowid
        TagManager.groups.append(TagGroup(obj_id, name))
        logging.info(f"New group '{name}' added to database")

    @staticmethod
    def deleteGroup(name):
        Database.CURSOR.execute(f'DELETE FROM tag_groups WHERE group_name="{name}"')
        Database.CONNECTION.commit()
        TagManager.groups.remove(name)
        logging.info(f"Group '{name}' removed from database")

    @staticmethod
    def renameGroup(name, new_name):
        Database.CURSOR.execute(f'UPDATE tag_groups SET group_name="{new_name}" WHERE group_name="{name}"')
        Database.CONNECTION.commit()
        ndx = TagManager.groups.index(name)
        TagManager.groups[ndx].name = new_name
        logging.info(f"Group '{name}' renamed to '{new_name}'")

    @staticmethod
    def newTag(name: str, group: TagGroup):
        Database.CURSOR.execute(f'INSERT INTO tags (tag_name, tag_group) VALUES ("{name}", {group.db_id})')
        Database.CONNECTION.commit()
        obj_id = Database.CURSOR.lastrowid
        new_tag = Tag(obj_id, name, group)
        TagManager.tags.append(new_tag)
        group.tags.append(new_tag)
        logging.info(f"New tag '{new_tag}' added to database")

    @staticmethod
    def deleteTag(name: str, group: TagGroup):
        Database.CURSOR.execute(f'DELETE FROM tags WHERE tag_name="{name}" AND tag_group={group.db_id}')
        Database.CONNECTION.commit()
        tag = f"{group.name} : {name}"
        TagManager.tags.remove(tag)
        group.tags.remove(tag)
        logging.info(f"Tag '{tag}' removed from database")

    @staticmethod
    def renameTag(name: str, group: TagGroup, new_name: str):
        Database.CURSOR.execute(f'UPDATE tags SET tag_name="{new_name}" WHERE tag_name="{name}" AND tag_group={group.db_id}')
        Database.CONNECTION.commit()
        tag = f"{group.name} : {name}"
        ndx = TagManager.tags.index(tag)
        TagManager.tags[ndx].name = new_name
        logging.info(f"Tag '{name}' renamed to '{new_name}'")


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
            # Database.CONNECTION.close()
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
            Database.CONNECTION.close()
            return
        # Check for column format mismatch
        for i in fmt_tables:
            Database.CURSOR.execute(f"PRAGMA table_info({i});")
            columns = {x[1] for x in Database.CURSOR.fetchall()}
            expected = {x for x in tables[i].keys() if 'FOREIGN' not in x and 'UNIQUE' not in x}    # TODO find better way to filter
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
        Database.TagManager._load_members()

        # Database program ready
        logging.info(f"Database '{path}' ready for operation.")

    @staticmethod
    def _createDB():
        # try:
        Database.CURSOR.executescript(tableTemplate)
        # print("Tables successfully created")
        # except sqlite3.OperationalError:
        #     print("One or more tables with the same name already exists.\nOperation Aborted.")
        pass

    @staticmethod
    def closeDB():
        # TODO close connection and purge objects from Managers (refresh and ready for new connection)
        pass
