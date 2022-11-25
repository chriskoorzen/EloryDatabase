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


class RootWidget(BoxLayout):
    pass


class EloryApp(App):

    def build(self):
        db.connect_db('database/known.db')              # Load db for use -> fragile dependency on "db" variable
        root = RootWidget()
        root.ids["tag_pane"].init_treeview()            # Populate Tags TreeView
        root.ids["file_nav"].init_database_tree()       # Populate Db Files TreeView
        return root

    # Dirty method of passing parameters between classes -> ideally do in build() method
    def on_start(self):
        self.title = "Elory - Elephant Memory File Manager"
        # print(self.root.children[0].children)
        # Child[0] = TagPane; Child[1] = FileDisplayPane; Child[2] = FileNavigationPane
        # Pass FileObject to Display Pane -> Select file for display
        callback = self.root.children[1].children[1].set_active_object              # get f() from FileDisplayPane
        self.root.children[1].children[2].bind(active_selected_file=callback)       # bind to prop of FileNavigationPane

        # Pass TagObject to DisplayPane -> Add new tags to files
        callback = self.root.children[1].children[1].get_selected_tag               # get f() from FileDisplayPane
        self.root.children[1].children[0].bind(selected_tag=callback)               # bind to prop of TagPane
        pass

    def on_stop(self):
        # introspect App properties
        print("App directory:", self.directory)
        print("User Data directory eg. settings, prefs etc. :", self.user_data_dir)


if __name__ == "__main__":
    EloryApp().run()
