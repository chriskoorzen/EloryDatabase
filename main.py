"""Test program"""
from databaseManagers import Database
import logging

logging.basicConfig(level=logging.DEBUG)

db = Database

# --- DB Connection Tests ---

# db.connectDB('root/screenshot.jpg')        # Connecting to file that is not sqlite db
# db.connectDB('unknown.db')                 # Connecting to database that does not exist (new file)
# add -> Connecting to database that does exist, but is empty
# add -> Connecting to database that does exist, tables match but columns do not
# add -> Connecting to database that does exist, tables match and columns match
# db.connectDB('elory.db')                   # Connecting to "foreign" database, tables match but columns do not
# add -> Connecting to "foreign" database, tables match and columns match


# db.FileManager.getFilesfromTags()
# print(db.TagManager.tags)

print("end of run.")
