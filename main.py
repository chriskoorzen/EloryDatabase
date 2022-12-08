from kivy.config import Config

Config.set("graphics", "width", 1200)
Config.set("graphics", "height", 720)
Config.set("graphics", "resizable", True)

from kivy import require as kivy_require
kivy_require("2.1.0")
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import DictProperty, ObjectProperty, StringProperty
from kivy.uix.settings import SettingsWithSidebar

from os import sep, getcwd
from os.path import expanduser, isfile

from elorydb import Database, db_logger, DatabaseError
from databaseObjects import TagGroup, File, object_logger
from modals import SelectSystemObject, Notification, UserInputWithOption
from displayTagPane import TagPane, tagpane_logger
from displayFileNavigator import FileNavigationPane, filenav_logger
from displayFilePane import FileDisplayPane, display_logger

_LOG_FILE = "newlogs.txt"

import sys
from traceback import format_tb
import logging
elory_logger = logging.getLogger("EloryApp")
db_logger.parent = elory_logger                 # There HAS to be a better way to do this?
object_logger.parent = elory_logger
filenav_logger.parent = elory_logger
tagpane_logger.parent = elory_logger
display_logger.parent = elory_logger


def log_uncaught_exception(e_type, e_value, e_traceback):
    elory_logger.critical("System crash...")
    elory_logger.critical(f"{e_type} {e_value}\n{''.join(format_tb(e_traceback))}")
    sys.__excepthook__(e_type, e_value, e_traceback)


sys.excepthook = log_uncaught_exception


class RootWidget(BoxLayout):
    APP_DIR = StringProperty()                          # Where app is located
    USER_DIR = StringProperty()                         # User's Home Directory

    current_db = StringProperty()                       # Hold path to current open db file

    db = ObjectProperty(Database())
    files = DictProperty({})
    groups = DictProperty({})
    tags = DictProperty({})

    def __init__(self, app_dir, user_dir, default_db, systemview, default_sort, default_view, app_config, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.APP_DIR = app_dir          # App's location and conf files
        self.USER_DIR = user_dir        # User home directory + Elory's directory

        self.ids["file_nav"].system_view_path = systemview
        self.ids["file_nav"].default_sort = default_sort
        self.ids["file_nav"].default_view = default_view

        if default_db == "":
            new_db = self.USER_DIR + sep + "elory"          # default name for a new database
            elory_logger.info("No default database set... Attempting to create new default database...")
            try:    # FIXME should probably first try to open, then create.
                self.db.create_new_db(new_db)
                elory_logger.info("New default database creation success. Updating config...")
                app_config.set("Basic Settings", "default_database_path", new_db + ".edb")
                app_config.write()
                self.load_database(new_db + ".edb")
            except DatabaseError:
                elory_logger.info("Creation failed... Fall back to opening default database...")
                success, msg = self.load_database(new_db + ".edb")
                if success:
                    elory_logger.info("Located default database success. Updating config...")
                    app_config.set("Basic Settings", "default_database_path", new_db + ".edb")
                    app_config.write()
                else:
                    elory_logger.error("Unable to create or load default database.")
        else:
            self.load_database(default_db)

    def on_kv_post(self, base_widget):
        pass

    def load_database(self, path):      # TODO can make this function a little less wasteful in its calls
        self.files.clear()              #   especially the clear calls and reloading objects of a previous db.
        self.tags.clear()
        self.groups.clear()

        try:
            self.db.connect_db(path)
        except DatabaseError as errmsg:
            self.ids["tag_pane"].load_objects()     # Calling load with empty dicts will clear view of previous widgets
            self.ids["file_nav"].load_objects()
            elory_logger.error(f"Fail to load Database '{path}' - {errmsg}")

            elory_logger.info(f"Attempting to revert to previous database...")
            if not self.current_db == "":
                elory_logger.info("Loading previous database...")
                self.load_database(self.current_db)
            else:
                elory_logger.warning(f"Failed to find previous database... Abort")
            return False, f"Failed to open database '{path}'\n\n{str(errmsg)}"
        self.current_db = path                      # Success - set path

        self.groups, self.tags = TagGroup.load_tag_collection(self.db)
        self.files = File.load_files(self.db, self.tags)

        self.ids["tag_pane"].load_objects()
        self.ids["file_nav"].load_objects()
        elory_logger.info("Environment load successful...")
        return True, None

    def open_db(self):
        def open_(*args):
            success, msg = self.load_database(args[1][0][0])
            if not success:
                n = Notification("Error", info=str(msg))
                n.open()

        # Open modal view and select a db file
        d = SelectSystemObject(heading="Select Database", submit_call=open_, path=self.APP_DIR, dirselect=False)
        d.open()

    def create_new_db(self):

        def create(*args):
            new_name, default_values = args[1]
            if not new_name.isalnum():
                message = "A database name may contain no special characters.\n\nPlease use names that contain " \
                          "letters and numbers only."
                n = Notification(heading="Database Name Error", info=message)
                n.open()
                elory_logger.warning(f"Failed database creation.. non-alphanumeric characters used")
                return

            default_values = True if default_values == "down" else False
            path = self.USER_DIR + sep + new_name
            new_db = self.db.create_new_db(path, default_values)
            elory_logger.info(f"Created new database '{new_name}' ...")
            self.load_database(new_db)

        info = "Choose new database name"
        d = UserInputWithOption(heading="Create New Database", info=info, submit_call=create)
        d.open()


class EloryApp(App):

    def build(self):
        elory_logger.info("App build initialize...")
        self.use_kivy_settings = False                  # Disable user management of Kivy Settings
        self.settings_cls = SettingsWithSidebar         # Select settings layout

        systemview = self.config.get("Basic Settings", "systemview_path")
        default_db = self.config.get("Basic Settings", "default_database_path")
        default_sort = self.config.get("Basic Settings", "default_sort_options")
        default_view = self.config.get("Basic Settings", "default_view_options")

        app_dir = self.config.get("App Settings", "APP_DIR")
        user_dir = self.config.get("App Settings", "USER_DIR")

        root = RootWidget(app_dir, user_dir,
                          default_db, systemview, default_sort, default_view, self.config)

        elory_logger.info("App build complete...")
        return root

    def on_start(self):
        elory_logger.info("App start...")
        self.title = "Elory - The Elephant Memory Database"

    def on_stop(self):
        # introspect App properties
        # print("App directory:", self.directory)
        # print("User Data directory eg. settings.json, prefs etc. :", self.user_data_dir)
        elory_logger.info("App closed...")

    def build_config(self, config):
        # Define config defaults
        # Read current defined configs
        # Create if not yet created
        # Fallback to logical defaults if values fail
        # Otherwise set to defined values
        self.directory
        elory_logger.info("Load config...")
        config.read("elory.ini")
        # config.setdefaults(
        #     "Basic Settings", {
        #         "systemview_path": "/home/student/PycharmProjects/elory",
        #         "default_database_path": "",
        #         "default_sort_options": "Tag",
        #         "default_view_options": "Database",
        #     }
        # )
        # config.setdefaults(
        #     "App Settings", {
        #         "APP_DIR": "/home/student/PycharmProjects/elory",     # "/home/student/.elory"
        #         "USER_DIR": "/home/student/Elory",                    # User's home + Elory's directory
        #         "SYSTEM": "unix"  # or, win
        #     }
        # )

    def build_settings(self, settings):
        # Define config GUI layout for user management
        settings.add_json_panel("Basic Settings",
                                config=self.config,
                                filename="resources/settings.json")

    def on_config_change(self, config, section, key, value):
        # Respond to changes in config settings
        elory_logger.info("Config updated...")
        print(config, section, key, value)


if __name__ == "__main__":
    elory_logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    handler = logging.StreamHandler()
    # handler = logging.FileHandler(_LOG_FILE)
    handler.setFormatter(fmt)
    elory_logger.addHandler(handler)
    # elory_logger.propagate = False
    EloryApp().run()
