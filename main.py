from databaseManagers import Database
import logging

logging.basicConfig(level=logging.DEBUG)

db = Database

db.connect_db('database/known.db')          # Connecting to database that does exist, tables match and columns match


print("\ntags: ")
for i in db.TagManager.tags.values():
    print(i)
print("\ngroups: ")
for i in db.TagManager.groups.values():
    print(i)
print("\nfiles: ")
for i in db.FileManager.files.values():
    print(i)

