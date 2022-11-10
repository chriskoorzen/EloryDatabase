"""Test program"""
from databaseManagers import Database
import logging
import hashlib

logging.basicConfig(level=logging.DEBUG)

db = Database

# --- DB Connection Tests ---

# db.connectDB('root/screenshot.jpg')        # Connecting to file that is not sqlite db
# db.connectDB('unknown.db')                 # Connecting to database that does not exist (new file)
# add -> Connecting to database that does exist, but is empty
# add -> Connecting to database that does exist, tables match but columns do not
db.connectDB('known.db')                   # Connecting to database that does exist, tables match and columns match
# db.connectDB('elory.db')                   # Connecting to "foreign" database, tables match but columns do not
# add -> Connecting to "foreign" database, tables match and columns match

# print(f"tags: {db.TagManager.tags}")
# print(f"groups: {db.TagManager.groups}")


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

res = db.FileManager.getFilesfromTag(db.TagManager.tags[3])
print(res)

print("end of run.")
