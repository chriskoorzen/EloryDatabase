from kivy.config import Config

Config.set("graphics", "width", 1200)
Config.set("graphics", "height", 720)
Config.set("graphics", "resizable", True)

from kivy import require as kivy_require
kivy_require("2.1.0")
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import DictProperty, ObjectProperty, StringProperty

import logging
logging.basicConfig(level=logging.DEBUG)
from os import sep, getcwd
from os.path import expanduser, isfile
from sqlite3 import DatabaseError

from elorydb import Database
from databaseObjects import TagGroup, Tag, File
from modals import SelectSystemObject, UserInputBox, Notification
from displayTagPane import TagPane
from displayFileNavigator import FileNavigationPane
from displayFilePane import FileDisplayPane


class RootWidget(BoxLayout):
    HOME_DIR = StringProperty()                         # User's Home Directory
    DATA_DIR = StringProperty()                         # HOME/'Elory': Store app data eg. databases
    APP_DIR = StringProperty()                          # Where app is located

    current_db = StringProperty()                       # Hold path to current open db file

    db = ObjectProperty(Database())
    files = DictProperty({})
    groups = DictProperty({})
    tags = DictProperty({})

    def __init__(self, home_dir, app_dir, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.HOME_DIR = home_dir
        self.DATA_DIR = home_dir + sep + "Elory"
        self.APP_DIR = app_dir
        print("RootWidget init")
        # print("RootWidget db:", hex(id(self.db)))
        # print("RootWidget files:", hex(id(self.files)))
        # print("RootWidget groups:", hex(id(self.groups)))
        # print("RootWidget tags:", hex(id(self.tags)))
        self.ids["file_nav"].change_system_view_path(self.HOME_DIR)

        # Create and load default Database if not exists
        if isfile(self.DATA_DIR + sep + "elory.edb"):            # TODO call load function if a current database exists
            print("File exists")
            self.load_database(self.DATA_DIR + sep + "elory.edb")

    def on_kv_post(self, base_widget):
        print("RootWidget on_kv_post")
        # print("RootWidget db:", hex(id(self.db)))
        # print("RootWidget files:", hex(id(self.files)))
        # print("RootWidget groups:", hex(id(self.groups)))
        # print("RootWidget tags:", hex(id(self.tags)))

        pass

    def load_database(self, path):
        self.files.clear()
        self.tags.clear()
        self.groups.clear()

        try:
            self.db.connect_db(path)
        except DatabaseError as emsg:
            self.ids["tag_pane"].load_objects()     # Calling load with empty dicts will clear view of previous widgets
            self.ids["file_nav"].load_objects()
            n = Notification("Error opening database", info=str(emsg))
            n.open()
            return
        self.current_db = path                      # Success - set path

        self.groups, self.tags = TagGroup.load_tag_collection(self.db)
        self.files = File.load_files(self.db, self.tags)

        self.ids["tag_pane"].load_objects()
        self.ids["file_nav"].load_objects()

    def open_db(self):
        def open_(*args):
            self.load_database(args[1][0])

        # Open modal view and select a db file
        d = SelectSystemObject(heading="Select Database", submit_call=open_, path=self.APP_DIR, dirselect=False)
        d.open()

    def create_new_db(self):

        def create(*args):
            new_name = args[1]
            path = self.DATA_DIR + sep + new_name
            new_db = self.db.create_new_db(path)
            self.load_database(new_db)

        info = "Choose new database name"
        d = UserInputBox(heading="Create New Database", info=info, submit_call=create)
        d.open()


class EloryApp(App):

    def build(self):
        print("App build start..")

        # Dev variables
        home_dir = "/home/student/PycharmProjects/elory"
        app_dir = "/home/student/PycharmProjects/elory"

        # Prod variables
        # home_dir = expanduser("~")
        # app_dir = getcwd()

        root = RootWidget(home_dir, app_dir)

        print("App build done..")
        return root

    def on_start(self):
        self.title = "Elory - The Elephant Memory Database"
        pass

    def on_stop(self):
        # introspect App properties
        # print("App directory:", self.directory)
        # print("User Data directory eg. settings, prefs etc. :", self.user_data_dir)
        pass


if __name__ == "__main__":
    EloryApp().run()
