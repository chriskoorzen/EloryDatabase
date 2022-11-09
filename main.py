"""Test program"""
from databaseManagers import Database

db = Database

db.connectDB('elory.db')        # Connecting to "foreign" database

db.FileManager.getFilesfromTags()

print(db.TagManager.tags)
