import pprint
import os

from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from pathlib import Path

from databaseManagers import Database as db
from sqlite3 import IntegrityError

# TODO Have consistency across database and system views in respect to tagged files -> a selected file on system view
#   should still reflect its tags. (Will possibly have to tweak FileChooser classes -> just the FileListEntry template)


class FileNavigationPane(RelativeLayout):
    active_selected_file = ObjectProperty()         # TODO This property really belongs in the displayFilePane
    DEFAULT_SYSTEM_FILE = StringProperty()

    def __init__(self, **kwargs):
        super(FileNavigationPane, self).__init__(**kwargs)
        self.DEFAULT_SYSTEM_FILE = "/home/student/PycharmProjects/elory"  # Where system view opens by default
        # str(Path.home())

        # self.current_system_file_nodes = dict()  # TODO not used currently

    def on_kv_post(self, base_widget):
        self.system_files_view = self.ids["system_files_view"]          # Get permanent references
        self.database_files_view = self.ids["db_box"]
                                        # TODO Create "strong" references through an Object property or similar method
        self.remove_widget(self.system_files_view)
        self.remove_widget(self.database_files_view)
        self.add_widget(self.system_files_view)  # Start default view on System Files Pane

    def init_database_tree(self):
        for file in db.FileManager.files.values():
            self.ids["db_tree"].add_file_node(file.path, file)

    def add_system_file_to_db(self, *args):
        # with dir_select to False, this should always only pass in files
        file_path = args[1]
        try:
            new_file = db.FileManager.add_file(file_path)   # Create new file in database -> this may throw errors
        except IntegrityError as errmsg:
            print(errmsg)
            print("Cannot add this file to database")
            return
        self.ids["db_tree"].add_file_node(file_path, new_file)

    def remove_file_from_db(self, *args):
        if self.ids["db_tree"].selected_node is None:
            return
        self.ids["db_tree"].remove_file_node(self.ids["db_tree"].selected_node)

    def set_active_file_object(self, selection):
        if type(selection) == FileNode:
            self.active_selected_file = selection.db_object   # Pass db object itself
            return
        if selection == []:
            return
        # Create 'anon' object on the fly with 'path' member
        # This is a workaround. Ideally we could have a single object represent a file, regardless if it was in
        # the database
        self.active_selected_file = type('anon', (object,), {"path": selection[0]})  # Pass 'anon' object

    def set_system_file_view(self, *args):
        # TODO unselect the active selected object when switching panes -> otherwise clicking has no effect
        # TODO this func and 'set_database_file_view' could probably be one
        if args[0].state == "normal":
            args[0].state = "down"
            return
        self.remove_widget(self.database_files_view)
        self.add_widget(self.system_files_view)

    def set_database_file_view(self, *args):
        if args[0].state == "normal":
            args[0].state = "down"
            return
        self.remove_widget(self.system_files_view)
        self.add_widget(self.database_files_view)

    def select_folder(self, *args):     # TODO not used currently
        def get_selection(*arg):
            print(user_selection.selection)
            return user_selection.selection
        user_selection = FileChooserIconView(size_hint=(1, 0.8), pos_hint={"top": 0.9}, path=str(Path.home()), dirselect=True)
        acceptBtn = Button(text="Submit")
        cancelBtn = Button(text="Cancel")
        btnBox = BoxLayout(orientation="horizontal", size_hint=(1, 0.2))
        btnBox.add_widget(cancelBtn)
        btnBox.add_widget(acceptBtn)
        contentBox = BoxLayout(orientation="vertical")
        contentBox.add_widget(user_selection)
        contentBox.add_widget(btnBox)
        popup = Popup(title='Create New Group',
                      content=contentBox,
                      size_hint=(0.9, 0.9))
        cancelBtn.bind(on_press=popup.dismiss)
        acceptBtn.bind(on_press=get_selection)
        acceptBtn.bind(on_release=popup.dismiss)
        popup.open()


class FileNode(TreeViewNode, BoxLayout):
    display_name = StringProperty()

    def __init__(self, db_object, **kwargs):
        super(FileNode, self).__init__(**kwargs)
        self.db_object = db_object
        self.display_name = self.db_object.name


class DatabaseTree(TreeView):

    def __init__(self, **kwargs):
        super(DatabaseTree, self).__init__(**kwargs)
        self.directory_layout = {}    # Flat dict -> key: file_path (incl directories), value: node

    def add_file_node(self, file_path, file_obj):
        path = file_path.split(os.sep)
        file_name = path.pop()
        full_dir = ''
        parent = None
        for directory in path:
            full_dir += (directory + os.sep)
            if full_dir not in self.directory_layout:                           # Directory does not exist
                dir_node = TreeViewLabel(text=directory, no_selection=True)     # Create node for directory
                self.directory_layout[full_dir] = dir_node      # Set reference between directory path and node
                super(DatabaseTree, self).add_node(dir_node, parent=parent)     # Add to tree
                self.toggle_node(dir_node)
                parent = dir_node                                   # Set node as parent for next folder in hierarchy
            else:   # Directory already exists
                parent = self.directory_layout[full_dir]    # Set node as parent for next folder in hierarchy
        full_dir += file_name               # Get path for file
        file_node = FileNode(file_obj)      # Create node for File
        self.directory_layout[full_dir] = file_node     # Set reference between path and file
        super(DatabaseTree, self).add_node(file_node, parent=parent)    # Add to Tree

    def remove_file_node(self, file_node):
        try:
            db.FileManager.remove_file(file_node.db_object.db_id)       # will return error is still tagged
        except IntegrityError as errmsg:
            print("Cannot delete tagged file", errmsg)
            return
        if len(file_node.parent_node.nodes) > 1:
            del self.directory_layout[file_node.db_object.path]
            super(DatabaseTree, self).remove_node(file_node)
        else:
            parent_path = file_node.db_object.path.rpartition(os.sep)   # TODO - very messy. Make better
            parent_path = parent_path[0] + parent_path[1]
            del self.directory_layout[parent_path]
            del self.directory_layout[file_node.db_object.path]
            super(DatabaseTree, self).remove_node(file_node.parent_node)
            super(DatabaseTree, self).remove_node(file_node)

    def sort_by_folder(self, *args):        # TODO Create custom load functions
        # Remove current nodes
        for node in self.root.nodes:
            self.remove_node(node)
        # List files by directory hierarchy

    def sort_by_tags(self, *args):          # TODO Create custom load functions
        # Remove current nodes
        for node in self.root.nodes:
            self.remove_node(node)
        # List files by tag hierarchy


def throwaway(*args):
    print("function executed", *args)
