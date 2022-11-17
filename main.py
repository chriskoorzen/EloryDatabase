from kivy.config import Config

Config.set("graphics", "width", 1200)
Config.set("graphics", "height", 720)
Config.set("graphics", "resizable", True)

from kivy import require as kivy_require
kivy_require("2.1.0")
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

import logging
logging.basicConfig(level=logging.DEBUG)

from databaseManagers import Database as db
from displayTagPane import TagPane
from displayFileNavigator import FileNavigationPane
from displayFilePane import FileDisplayPane

# Not ideal -> because at some point "path" is a variable argument inside the app, to open and close databases
db.connect_db('database/known.db')          # Connecting to database that does exist, tables match and columns match


class RootWidget(BoxLayout):
    pass


class EloryApp(App):
    def build(self):
        return RootWidget()

    # Dirty method of passing parameters between classes -> ideally do in build() method
    def on_start(self):
        # print(self.root.children[0].children)
        # Child[0] = TagPane, Child[1] = FileDisplayPane, Child[2] = FileNavigationPane
        # Pass FileObject to Display Pane
        callback = self.root.children[0].children[1].set_active_object              # FileDisplayPane
        self.root.children[0].children[2].bind(active_selected_file=callback)       # FileNavigationPane

        # Pass TagObject to DisplayPane
        callback = self.root.children[0].children[1].get_selected_tag               # FileDisplayPane
        self.root.children[0].children[0].bind(selected_tag=callback)               # TagPane
        pass


if __name__ == "__main__":
    EloryApp().run()
