from kivy.app import App
from kivy.uix.widget import Widget

from databaseManagers import Database as db
import logging
logging.basicConfig(level=logging.DEBUG)

db.connect_db('database/known.db')          # Connecting to database that does exist, tables match and columns match


class RootWidget(Widget):
    pass


class EloryApp(App):
    def build(self):
        return RootWidget()


if __name__ == "__main__":
    EloryApp().run()
