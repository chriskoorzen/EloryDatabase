"""Test program"""
import unittest
import sqlite3
import os
from elorydb import Database, db_logger


# --- DB Connection Tests ---
class TestDataBaseConnections(unittest.TestCase):

    # Case 1: Connecting to database that does not exist (new file)
    def test_create_new_file_if_file_not_exists(self):
        non_existent_db = 'database/does_not_exist.db'
        self.assertFalse(os.path.isfile(non_existent_db))   # File does not exist
        with self.assertLogs(db_logger, "WARNING") as lg:
            Database.connect_db(non_existent_db)

        # Expecting 2 Warning messages
        self.assertEqual(lg.records[0].getMessage(),
            f"File '{non_existent_db}' does not exist. Creating new sqlite3 database")
        self.assertEqual(lg.records[1].getMessage(),
            f"Database '{non_existent_db}' is empty... Auto creating tables...")
        self.assertTrue(os.path.isfile(non_existent_db))    # File exists
        self.addCleanup(os.remove, non_existent_db)

    # Case 2: Connecting to file that is not sqlite db
    def test_reject_invalid_file_connection(self):
        invalid_file = 'database/screenshot.jpg'
        self.assertTrue(os.path.isfile(invalid_file))       # File exists
        with self.assertRaises(sqlite3.DatabaseError):
            Database.connect_db(invalid_file)

    # Case 3: Connected to empty file ->
    def test_create_new_database_if_file_empty(self):
        empty_file = 'database/empty_file'
        with open(empty_file, 'w') as f:                    # Create empty file
            f.close()
        self.assertTrue(os.path.isfile(empty_file))         # Exists
        with open(empty_file, 'r') as f:
            data = f.read()
            self.assertEqual(len(data), 0)                  # File is empty
        with self.assertLogs(db_logger, "WARNING") as lg:   # Issues warning
            Database.connect_db(empty_file)
        self.assertEqual(lg.records[0].getMessage(),        # Expecting 1 Warning message
            f"Database '{empty_file}' is empty... Auto creating tables...")
        CON = sqlite3.connect(empty_file)
        CUR = CON.cursor()
        CUR.execute("PRAGMA schema_version")
        self.assertNotEqual(0, CUR.fetchone()[0])           # This is a valid sqlite3 db -> returns 0 otherwise
        CON.close()
        self.addCleanup(os.remove, empty_file)


    # db.connectDB('unknown.db')
    # add -> Connecting to database that does exist, tables match but columns do not
    # db.connectDB('database/known.db')          # Connecting to database that does exist, tables match and columns match
    # db.connectDB('elory.db')                   # Connecting to "foreign" database, tables match but columns do not
    # add -> Connecting to "foreign" database, tables match and columns match

    # print(f"tags: {db.TagManager.tags}")
    # print(f"groups: {db.TagManager.groups}")
    pass


# print("\ntags: ")
# for i in db.TagManager.tags.values():
#     print(i)
# print("\ngroups: ")
# for i in db.TagManager.groups.values():
#     print(i)
# print("\nfiles: ")
# for i in db.FileManager.files.values():
#     print(i)

# --- Operational Tests ---

# --- Tag Manager Tests ---
# db.TagManager.newGroup("Emotion")           # Add new TagGroup to Database
# db.TagManager.newGroup("Emotion")           # Try adding existing TagGroup to Database
# print(f"groups: {db.TagManager.groups}")

# db.TagManager.deleteGroup("Emotion")        # Remove existent group from database
# print(f"groups: {db.TagManager.groups}")

# db.TagManager.renameGroup("Config Files", "Settings")
# print(f"groups: {db.TagManager.groups}")


# db.TagManager.newTag("Eagle", db.TagManager.groups[2])
# print(f"tags: {db.TagManager.tags}")
#
# db.TagManager.deleteTag("Eagle", db.TagManager.groups[2])
# print(f"groups: {db.TagManager.tags}")
#
# db.TagManager.renameTag("Dog", db.TagManager.groups[2], "Canine")
# print(f"groups: {db.TagManager.tags}")

# --- File Manager Tests ---

# db.FileManager.addFile("root/screenshot.jpg")
# db.FileManager.addFile("root/fake_but_same.jpg")          # Add identical file with different names

# db.FileManager.addFile("root/bullshit/more_bullshit/fakefile.jpg")


# db.FileManager.removeFile("root/screenshot_copy.jpg")
# print("file removed")

# db.FileManager.addFileTag("root/bullshit/more_bullshit/fakefile.jpg", db.TagManager.tags[3])

# db.FileManager.removeFileTag("root/bullshit/more_bullshit/fakefile.jpg", db.TagManager.tags[3])

# res = db.FileManager.getFilesfromTag(db.TagManager.tags[3])

print("end of run.")
