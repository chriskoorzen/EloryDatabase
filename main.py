from kivy.config import Config

Config.set("graphics", "width", 1200)
Config.set("graphics", "height", 600)
Config.set("graphics", "resizable", True)

from kivy import require as kivy_require
kivy_require("2.1.0")
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

import logging
logging.basicConfig(level=logging.DEBUG)

from databaseManagers import Database as db
from displayTagPane import TagPane

# Not ideal -> because at some point "path" is a variable argument inside the app, to open and close databases
db.connect_db('database/known.db')          # Connecting to database that does exist, tables match and columns match


class RootWidget(BoxLayout):
    pass


class EloryApp(App):
    def build(self):
        return RootWidget()


if __name__ == "__main__":
    EloryApp().run()
