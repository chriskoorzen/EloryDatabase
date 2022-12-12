from sqlite3 import DatabaseError, IntegrityError, connect
import os.path
import hashlib
from pathlib import PurePath

import logging
db_logger = logging.getLogger(__name__)
# db_logger.setLevel(logging.DEBUG)
# fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
# handler = logging.StreamHandler()
# handler.setFormatter(fmt)
# db_logger.addHandler(handler)
# db_logger.propagate = False


class Database:
    _DEFINITION = {  # {
        "files": (  # table_name: (
            {"file_id": "INTEGER PRIMARY KEY",  # {column_name: column_definition},
             "file_path": "TEXT UNIQUE NOT NULL",  # {constraint: constraint_definition}
             "file_hash_name": "TEXT UNIQUE NOT NULL"},  # ),
            {}  # }
        ),
        "tag_groups": (
            {"group_id": "INTEGER PRIMARY KEY",
             "group_name": "TEXT UNIQUE NOT NULL"},
            {}
        ),
        "tags": (
            {"tag_id": "INTEGER PRIMARY KEY",
             "tag_name": "TEXT NOT NULL",
             "tag_group": "INTEGER NOT NULL"},
            {"FOREIGN KEY(tag_group)": "REFERENCES tag_groups(group_id) ON DELETE RESTRICT ON UPDATE CASCADE",
             "UNIQUE(tag_name, tag_group)": "ON CONFLICT FAIL"}
        ),
        "tagged_files_m2m": (
            {"tag": "INTEGER NOT NULL",
             "file": "INTEGER NOT NULL"},
            {"FOREIGN KEY(tag)": "REFERENCES tags(tag_id) ON DELETE RESTRICT ON UPDATE CASCADE",
             "FOREIGN KEY(file)": "REFERENCES files(file_id) ON DELETE RESTRICT ON UPDATE CASCADE",
             "UNIQUE(tag, file)": "ON CONFLICT FAIL"}
        )
    }
    _DEFAULT_VALUES = {  # groups: [tags]
        "People": ["Jack Pembleton", "Benoit Blanc", "Kimberly Mathis"],
        "Places": ["New York", "Livingstone Beach", "Frontier National Park", "Modena Vacation Home"],
        "Pets": ["Leah -Dog", "Luna -Cat", "Jack -Bird"]
    }
    _FILE_IDENTIFIER = ".edb"  # elory database

    DATA_DIR = ''
    CONN = None
    CURS = None

    def __init__(self, path=None, create_new=None, data_dir=None):
        # Data directory -> The database storage location. Defaults to cwd
        # Path -> shorthand for "connect to db"
        # Create new -> Shorthand for "create new db" at "path"
        self.DATA_DIR = os.getcwd() if (data_dir is None or not os.path.isdir(data_dir)) else data_dir
        # self.PATH = path

    def _prepare_path(self, path):
        # Allow user to specify a custom absolute path
        proposed = PurePath(path)
        if proposed.is_absolute():  # Not a relative path name
            if os.path.exists(os.path.dirname(path)):  # The directory actually exists
                # TODO strip any "." suffixes
                return path + self._FILE_IDENTIFIER
            raise DatabaseError  # Absolute path by semantics, but parent dir does not exist
        # else, take relative name and append to specified data directory
        path = self.DATA_DIR + os.sep + path + self._FILE_IDENTIFIER  # Take
        return path

    def _build_tables(self, default_values=True):
        table_template = "BEGIN;\n"  # SQL script start
        for table in self._DEFINITION.keys():
            table_template += f"CREATE TABLE {table}("  # Open Table definition
            for column in self._DEFINITION[table][0].keys():
                table_template += f"{column} {self._DEFINITION[table][0][column]}, "  # Add columns
            for constn in self._DEFINITION[table][1].keys():
                table_template += f"{constn} {self._DEFINITION[table][1][constn]}, "  # Add constraints
            table_template = table_template.rstrip(", ") + ");\n"  # close table definition
        table_template += "COMMIT;\n"  # SQL script end
        self.CURS.executescript(table_template)
        db_logger.info(f"Initialized tables for database '{self.PATH}'")
        if default_values:
            groups = []
            tags = []
            for key in self._DEFAULT_VALUES.keys():
                groups.append({"group_name": key})
            group_ids = self.create_entry("group", groups)
            groups = [[y for y in x.values()][0] for x in groups]       # FIXME a consequence of the unintuitive DB API
            for g in zip(groups, group_ids):
                for tag in self._DEFAULT_VALUES[g[0]]:
                    tags.append({'tag_name': tag, 'group': g[1][1]})
            self.create_entry("tag", tags)
            db_logger.info(f"Initialized default values for database '{self.PATH}'")

    def _disconnect(self):
        if self.CONN is not None:
            self.CONN.close()
            db_logger.info(f"Database '{self.PATH}' closed.")

    def _definition_exists(self):
        # Check if required tables are present
        self.CURS.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        db_tables = {x[0] for x in self.CURS.fetchall()}
        fmt_tables = {x for x in self._DEFINITION.keys()}
        if not fmt_tables <= db_tables:
            # format tables is not present in (subset of) database...
            errmsg = "Required tables not present in database"
            db_logger.warning(f"{errmsg} '{self.PATH}'")
            return False
        if len(db_tables) > len(fmt_tables):  # Warn if foreign tables are present
            db_logger.warning(f"Unrecognized tables detected in database '{self.PATH}'")

        # Check for column format mismatch
        for i in fmt_tables:
            self.CURS.execute(f"PRAGMA table_info({i});")
            columns = {x[1] for x in self.CURS.fetchall()}
            # TODO find better way to filter FOREIGN and UNIQUE constraint definitions -> the below method is fragile
            expected = {x for x in self._DEFINITION[i][0].keys()}
            # expected = {x for x in self._DEFINITION[i].keys() if 'FOREIGN' not in x and 'UNIQUE' not in x}
            if not columns == expected:
                errmsg = "Tables exist but do not match the required column formats in database"
                db_logger.warning(f"{errmsg} '{self.PATH}'")
                return False
        db_logger.info(f"Table formats OK in database '{self.PATH}'")
        return True  # All checks passed

    @staticmethod
    def digest(file):       # FIXME this function stalls hard on external files (Linux tested)
        """Return a unique hash code of a given file.

        The return must be unique to the file itself, should be platform-agnostic and resilient to meta-data changes.
        The goal is to identify a particular file (defined as a series of bits) regardless of the OS, underlying fs,
        or system architecture.
        """
        # Hash times
        # 19  MB ~ 0.04 sec
        # 200 MB ~ 0.31 sec
        # 400 MB ~ 0.61 sec
        # 600 MB ~ 0.9 sec
        # 900 MB ~ 1.35 sec
        # 4.3 GB ~ 6.3 sec      # TODO will very much have to make this an async function
        if not os.path.isfile(file):
            db_logger.warning(f"{file} is not a valid file")
            return False
        h = hashlib.md5()
        b = bytearray(128 * 1024)
        mv = memoryview(b)  # using memoryview, we can slice a buffer without copying it
        with open(file, 'rb', buffering=0) as file_obj:
            while n := file_obj.readinto(mv):
                h.update(mv[:n])
        return h.hexdigest()

    # Database management
    def create_new_db(self, path, default_values=True):
        db_logger.info(f"Creating new database '{path}'...")
        # TODO reject names with special characters
        if os.path.isfile(path):  # reject existing files
            # TODO or directories must also be rejected
            db_logger.error(f"File '{path}' already exists.")
            raise DatabaseError

        self.PATH = self._prepare_path(path)  # Set path, and new file name

        self.CONN = connect(self.PATH)  # Create (connect) new sqlite3 database
        self.CURS = self.CONN.cursor()

        self._build_tables(default_values)  # Build database

        # Necessary settings for database
        self.CURS.execute("PRAGMA foreign_keys = ON")  # Enforce Foreign Key constraints
        self.CONN.commit()
        db_logger.info(f"Database '{self.PATH}' creation complete and ready for operation")
        return self.PATH

    def connect_db(self, path):

        if not os.path.isfile(path):  # Reject non-files
            db_logger.error(f"File '{path}' does not exist.")
            raise DatabaseError

        self._disconnect()
        self.PATH = path
        self.CONN = connect(self.PATH)  # Connect to existing file
        self.CURS = self.CONN.cursor()

        # Check if file is valid sqlite3 database
        self.CURS.execute("PRAGMA schema_version")  # Will fail with 'DatabaseError' if invalid file
        db_logger.info(f"Connecting to database '{self.PATH}' ...")

        # Is this db empty?
        if self.CURS.fetchone()[0] == 0:  # Database is valid but empty -> abort connection
            errmsg = f"Database '{self.PATH}' is empty. Abort connection."
            db_logger.error(errmsg)
            self._disconnect()
            raise DatabaseError(errmsg)

        if not self._definition_exists():  # Does it have the necessary tables and columns?
            errmsg = f"Database '{self.PATH}' data format mismatch. Abort connection."
            db_logger.error(errmsg)
            self._disconnect()
            raise DatabaseError(errmsg)

        # Necessary settings for database
        self.CURS.execute("PRAGMA foreign_keys = ON")  # Enforce Foreign Key constraints
        self.CONN.commit()
        db_logger.info(f"Database '{self.PATH}' connected and ready for operation.")

    def extend_db(self, path, default_values=True):

        if not os.path.isfile(path):  # Reject non-files
            db_logger.error(f"File '{path}' does not exist.")
            raise DatabaseError

        self._disconnect()
        self.PATH = path
        self.CONN = connect(self.PATH)  # Connect to existing file
        self.CURS = self.CONN.cursor()

        # Check if file is valid sqlite3 database
        self.CURS.execute("PRAGMA schema_version")  # Will fail with 'DatabaseError' if invalid file
        db_logger.info(f"Connected to database '{self.PATH}' ...")

        if self._definition_exists():
            errmsg = f"Database '{self.PATH}' data format already exists. Abort extension."
            db_logger.error(errmsg)
            self._disconnect()
            raise DatabaseError(errmsg)

        self._build_tables(default_values)

        # Necessary settings for database
        self.CURS.execute("PRAGMA foreign_keys = ON")  # Enforce Foreign Key constraints
        self.CONN.commit()
        db_logger.info(f"Extension of database '{self.PATH}' successful and ready for operation")

    # CRUD operations
    # TODO could probably modify to take any kind and number of valid items and do batch ops
    #   because ideally we'd like to minimize disk writes and reads.
    def create_entry(self, item, values: list):
        """
        item -> specify the type of entry to make.      options: "file", "group", "tag"
        values -> a list of dicts containing the parameters of the specified item
            "file" : {
                'file_path': 'path to file object'
            }
            "group" : {
                'group_name': 'name for a new group'
            }
            "tag" : {
                'tag_name': 'name for new tag',
                'group': int id of group                  -> in future support 'group_name' as txt
            }
            "tag-file": {
                'file_id': int file_id
                'tag_id':  int tag_id
            }
        returns a list (in order) of newly created items id's or True -> if an entry failed, None (or False?) instead
        """
        # Relying on the cur.execute (?) replacement method for input sanitization

        if item not in ["file", "group", "tag", "tag-file"]:  # self._DEFINITION.keys()
            errmsg = f"Item '{item}' is not a valid database object"
            db_logger.error(errmsg)
            raise IntegrityError(errmsg)

        # TODO unfortunately, cur.execute only stores the last rowid of a newly created item, so we will have to call
        #   the function iteratively. Perhaps create a custom sql func that can return the list of a batch transaction?

        if item == "file":
            newly_created_files = []
            for new_file in values:  # Iterate over list of dicts
                unique_hash = self.digest(new_file['file_path'])  # return false if not valid path. else hash
                if not unique_hash:
                    newly_created_files.append((False, f"{new_file['file_path']} is not a valid file."))
                    continue
                try:
                    self.CURS.execute("INSERT INTO files (file_path, file_hash_name) VALUES (?, ?)",
                                      (os.path.abspath(new_file['file_path']), unique_hash))
                except IntegrityError as errmsg:
                    # sqlite3 is ambiguous about UNIQUE constraints - it doesn't seem to have a set order - sometimes
                    # it'll return a file_path error, other times a file_hash error for a file that violates both, so
                    # it's hard to know which constraint was actually violated in the case of a file that violates only
                    # one. Some additional checking is required by the caller to verify.
                    db_logger.error(errmsg)
                    newly_created_files.append((False, errmsg, unique_hash))
                    continue
                self.CONN.commit()
                newly_created_files.append((self.CURS.lastrowid, unique_hash))
                db_logger.info(f"Added file '{new_file['file_path']}' to database")
            return newly_created_files

        if item == "group":
            newly_created_groups = []
            for new_group in values:  # Iterate over list of dicts
                # TODO santitize new_group['group_name']
                try:
                    self.CURS.execute("INSERT INTO tag_groups (group_name) VALUES (?)",
                                      (new_group["group_name"], ))
                except IntegrityError as errmsg:
                    db_logger.error(errmsg)
                    newly_created_groups.append((False, errmsg))
                    continue
                self.CONN.commit()
                newly_created_groups.append((True, self.CURS.lastrowid))
                db_logger.info(f"New group '{new_group['group_name']}' added to database")
            return newly_created_groups

        if item == "tag":
            newly_created_tags = []
            for new_tag in values:  # Iterate over list of dicts
                # group = new_tag['group']
                # if type(group) != int:                # TODO support group names as txt in future
                try:
                    self.CURS.execute("INSERT INTO tags (tag_name, tag_group) VALUES (?, ?)",
                                      (new_tag['tag_name'], new_tag['group']))
                except IntegrityError as errmsg:
                    db_logger.error(errmsg)
                    newly_created_tags.append((False, errmsg))
                    continue
                self.CONN.commit()
                newly_created_tags.append((True, self.CURS.lastrowid))
                db_logger.info(f"New tag '{new_tag['tag_name']}' added to database")
            return newly_created_tags

        if item == "tag-file":
            newly_linked_tag_files = []
            for link in values:
                try:
                    self.CURS.execute("INSERT INTO tagged_files_m2m (tag, file) VALUES (?, ?)",
                                      (link['tag_id'], link['file_id']))
                except IntegrityError as errmsg:
                    db_logger.error(errmsg)
                    newly_linked_tag_files.append((False, errmsg))
                    continue
                self.CONN.commit()
                newly_linked_tag_files.append((link['tag_id'], link['file_id']))    # tuple of tag-file pairs
                db_logger.info(f"Linked tag '{link['tag_id']}' to file '{link['file_id']}'")
            return newly_linked_tag_files

    def read_entry(self, values: list = []):    # FIXME this is a very messy operation - unreadable
        """
        values        = [ (entry_to_read, by_parameter, parameter_value  ), ... ]
        entry to read = specify the type      valid options: "files", "tag_groups", "tags"
        returns a list of requested items in order
        "files" : {
            'all': None                                 -> return all files                                 (list)
            'file_path': str,
            'file_hash_name': str,
            'file_id': int,                             -> return the matching file object                  (tuple)
            'tag_id': int,                              -> returns all files associated with this tag       (list)
            'group_id': int,                                                                                            # TODO Future
            'group_name': str                           -> returns all files associated with this group     (list)      # TODO Future
        }
        "tag_groups" : {
            'all': None                                 -> return all groups                                (list)
            'group_name': str,
            'group_id': int,                            -> return the matching group object                 (tuple)
            'tag_id': int,                              -> return the matching group object                 (tuple)
            'tag_name': str,                            -> return all groups associated with this tag name  (list)
            'file_id': int,                                                                                             # TODO Future
            'file_hash_name': str,                                                                                      # TODO Future
            'file_path': str,                           -> return all groups associated with this file      (list)      # TODO Future
        }
        "tags" : {
            'all': None                                 -> return all tags                                  (list)
            'tag_id': int tag_id                        -> return the matching tag object                   (tuple)
            'tag_name': str 'tag name'                  -> return all tags associated with this name        (list)
            'file_id': int,
            'file_hash_name': str,
            'file_path': str,                           -> return all tags associated with this file        (list)
            'group_id': int,
            'group_name': str                           -> return all tags associated with this group       (list)
        }
        """
        valid_props = {'group_id', 'group_name', 'tag_id', 'tag_name', 'file_id', 'file_hash_name', 'file_path', 'tag_group', 'file'}
        valid_items = {"files", "tag_groups", "tags"}
        results = []
        for entry in values:  # Expect a tuple ( "item", "property", "prop_value" )
            if entry[0] in valid_items:
                if entry[1] == 'all':  # return all items of type
                    self.CURS.execute(f"SELECT * FROM {entry[0]}")
                    res = self.CURS.fetchall()
                    ans = []
                    for item in res:
                        if entry[0] == "files":
                            self.CURS.execute(f"SELECT tag FROM tagged_files_m2m WHERE file='{item[0]}'")
                            ans.append((*item, [x[0] for x in self.CURS.fetchall()]))
                        if entry[0] == "tags":
                            self.CURS.execute(f"SELECT file FROM tagged_files_m2m WHERE tag='{item[0]}'")
                            ans.append((*item, [x[0] for x in self.CURS.fetchall()]))
                        if entry[0] == "tag_groups":
                            self.CURS.execute(f"SELECT tag_id FROM tags WHERE tag_group='{item[0]}'")
                            ans.append((*item, [x[0] for x in self.CURS.fetchall()]))
                    results.append(ans)

                elif entry[1] in valid_props:
                    if entry[1] in self._DEFINITION[entry[0]][0]:  # inside its own table
                        self.CURS.execute(f"SELECT * FROM {entry[0]} WHERE {entry[1]}='{entry[2]}'")
                        results.append(self.CURS.fetchall())

                    elif (entry[0] == "files") and (entry[1] == "tag_id"):  # m2m tag-file query
                        self.CURS.execute(f"SELECT file, tag FROM tagged_files_m2m WHERE tag='{entry[2]}'")
                        results.append(self.CURS.fetchall())

                    elif (entry[0] == "tags") and ("file" in entry[1]):  # m2m tag-file query
                        self.CURS.execute(f"SELECT tag, file FROM tagged_files_m2m WHERE file='{entry[2]}'")
                        results.append(self.CURS.fetchall())

                    # elif (entry[0] == "files") and ("group" in entry[1]):          # Cross query - get files from group
                    #     self.CURS.execute(
                    #         f"SELECT * FROM {entry[0]} WHERE file_id='{entry[2]}'")
                    #     results.append(self.CURS.fetchall())
                    #
                    # elif (entry[0] == "tag_groups") and ("file" in entry[1]):      # Cross query - get groups from file
                    #     pass
                    else:
                        errmsg = f"Retrieve '{entry[0]}' for property '{entry[1]}' not yet implemented"
                        db_logger.warning(errmsg)
                        results.append(None)
                else:
                    errmsg = f"'{entry[1]}' is not a valid property of {entry[0]}"
                    db_logger.error(errmsg)
                    results.append(None)
            else:
                errmsg = f"Item '{entry[0]}' is not a valid database object"
                db_logger.error(errmsg)
                results.append(None)
        return results

        # First implementation -> # TODO Refine the API to make sense across the CRUD ops
        # if item not in ["file", "group", "tag"]:  # self._DEFINITION.keys()
        #     errmsg = f"Item '{item}' is not a valid database object"
        #     db_logger.error(errmsg)
        #     raise IntegrityError(errmsg)
        #
        # # TODO currently it is possible to specify items with different keywords, and have to iteratively loop over them
        # #   and return. Write a sql join (or similar concept) function that can process a batch at once.
        #
        # if item == "file":
        #     if len(values) == 0:
        #         self.CURS.execute(f"SELECT file_id, file_path, file_hash_name FROM files")
        #         return self.CURS.fetchall()
        #     requested_files = []
        #     for req_file in values:
        #         # valid file properties = {'file_id', 'file_path', 'file_hash_name'}
        #         prop = req_file.keys() & {'file_id', 'file_path', 'file_hash_name'}
        #         if len(prop) == 0:
        #             db_logger.error(f"No valid file properties given: {req_file}")
        #             requested_files.append(None)
        #             continue
        #         col = prop.pop()
        #         try:
        #             self.CURS.execute(f"SELECT file_id, file_path, file_hash_name FROM files WHERE {col}='{req_file[col]}'")
        #         except Exception as e:          # Not too certain what all we may get here
        #             db_logger.error(f"Error '{e}' occurred during retrieval call for file object {req_file}")
        #             requested_files.append(None)
        #             continue
        #         requested_files.extend(self.CURS.fetchall())        # return tuple objects for unique identifiers
        #     return requested_files
        #
        # if item == "group":
        #     if len(values) == 0:
        #         self.CURS.execute(f"SELECT group_id, group_name FROM tag_groups")
        #         return self.CURS.fetchall()
        #     requested_groups = []
        #     for req_group in values:
        #         # valid file properties = {'group_id', 'group_name'}
        #         prop = req_group.keys() & {'group_id', 'group_name'}
        #         if len(prop) == 0:
        #             db_logger.error(f"No valid group properties given: {req_group}")
        #             requested_groups.append(None)
        #             continue
        #         col = prop.pop()
        #         try:
        #             self.CURS.execute(f"SELECT group_id, group_name FROM tag_groups WHERE {col}='{req_group[col]}'")
        #         except Exception as e:          # Not too certain what all we may get here
        #             db_logger.error(f"Error '{e}' occurred during retrieval call for group object {req_group}")
        #             requested_groups.append(None)
        #             continue
        #         requested_groups.extend(self.CURS.fetchall())
        #
        # if item == "tag":
        #     if len(values) == 0:
        #         self.CURS.execute(f"SELECT tag_id, tag_name, tag_group FROM tags")
        #         return self.CURS.fetchall()
        #     requested_tags = []
        #     for req_tag in values:
        #         properties = req_tag.keys()
        #         if "tag_id" in properties:      # get a unique tag by its id
        #             try:
        #                 self.CURS.execute(f"SELECT tag_id, tag_name, tag_group FROM tags WHERE tag_id='{req_tag['tag_id']}'")
        #             except Exception as e:  # Not too certain what all we may get here
        #                 db_logger.error(f"Error '{e}' occurred during retrieval call for tag object {req_tag}")
        #                 requested_tags.append(None)
        #                 continue
        #             requested_tags.extend(self.CURS.fetchall())
        #             continue
        #         if {"tag_name", "tag_group"} <= properties:     # Both properties need to be present to identify unique object
        #             try:
        #                 self.CURS.execute(
        #                     f"SELECT tag_id, tag_name, tag_group FROM tags WHERE tag_name='{req_tag['tag_name']}' AND tag_group='{req_tag['tag_group']}'")
        #             except Exception as e:  # Not too certain what all we may get here
        #                 db_logger.error(f"Error '{e}' occurred during retrieval call for tag object {req_tag}")
        #                 requested_tags.append(None)
        #                 continue
        #             requested_tags.extend(self.CURS.fetchall())
        #             continue

    def update_entry(self, item, values: list):
        # """
        # """
        #
        # if item not in ["file", "group", "tag"]:        # self._DEFINITION.keys()
        #     errmsg = f"Item '{item}' is not a valid database object"
        #     db_logger.error(errmsg)
        #     raise IntegrityError(errmsg)
        #
        # if item == "file":
        #
        # if item == "group":
        #     Database.CURSOR.execute(f'UPDATE tag_groups SET group_name="{new_name}" WHERE group_id={g.db_id}')
        #     Database.CONNECTION.commit()
        #     db_logger.info(f"Group '{g.name}' renamed to '{new_name}'")
        #
        # if item == "tag":
        #     Database.CURSOR.execute(f'UPDATE tags SET tag_name="{new_name}" WHERE tag_id={t.db_id}')
        #     Database.CONNECTION.commit()
        #     db_logger.info(f"Tag '{t.name}' renamed to '{new_name}'")
        pass

    def delete_entry(self, item, values: list):
        """
        item -> specify the type of entry to make.      options: "file", "group", "tag"
        values -> a list of dicts containing the parameters of the specified item
            "file" : {'file_id': int}
            "group" : {'group_id': int}
            "tag" : {'tag_id': int}
        returns a list (in order) of "True" if deletion succeeded -> else "False"
        """

        if item not in ["file", "group", "tag", "tag-file"]:  # self._DEFINITION.keys()
            errmsg = f"Item '{item}' is not a valid database object"
            db_logger.error(errmsg)
            raise IntegrityError(errmsg)

        if item == "file":
            # TODO Should be able to delete files even if tagged.
            success_resp = []
            for rem_file in values:  # dict - prop_identifier (always "id")
                try:
                    # This SQL should cascade auto
                    self.CURS.execute(f"DELETE FROM files WHERE file_id='{rem_file['file_id']}'")
                except IntegrityError as errmsg:
                    db_logger.error(errmsg)
                    success_resp.append((False, errmsg))
                    continue
                self.CONN.commit()
                db_logger.info(f"Removed file '{rem_file['file_id']}' from database")
                success_resp.append((True, ))
            return success_resp

        if item == "group":
            success_resp = []
            for rem_group in values:  # dict - prop_identifier (always "id")
                try:
                    self.CURS.execute(f"DELETE FROM tag_groups WHERE group_id='{rem_group['group_id']}'")
                except IntegrityError as errmsg:
                    db_logger.error(errmsg)
                    success_resp.append((False, errmsg))
                    continue
                self.CONN.commit()
                db_logger.info(f"Group '{rem_group['group_id']}' removed from database")
                success_resp.append((True, ))
            return success_resp

        if item == "tag":
            # Must not be able to delete tags attached to files
            success_resp = []
            for rem_tag in values:  # dict - prop_identifier (always "id")
                try:
                    self.CURS.execute(f"DELETE FROM tags WHERE tag_id='{rem_tag['tag_id']}'")
                except IntegrityError as errmsg:
                    db_logger.error(errmsg)
                    success_resp.append((False, errmsg))
                    continue
                self.CONN.commit()
                db_logger.info(f"Tag '{rem_tag['tag_id']}' removed from database")
                success_resp.append((True, ))
            return success_resp

        if item == "tag-file":
            success_resp = []
            for unlink in values:  # dict - prop_identifier (always "id")
                try:
                    self.CURS.execute(
                        f"DELETE FROM tagged_files_m2m WHERE tag='{unlink['tag_id']}' AND file='{unlink['file_id']}'")
                except IntegrityError as errmsg:
                    db_logger.error(errmsg)
                    success_resp.append((False, errmsg))
                    continue
                self.CONN.commit()
                db_logger.info(f"Untagged file '{unlink['file_id']}' from tag '{unlink['tag_id']}'")
                success_resp.append((True, ))
            return success_resp

    # Files

    # TODO Utility function to integrity check file_path, while keeping file_hash consistent ->
