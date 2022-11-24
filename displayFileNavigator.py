import pprint
import os
from collections import deque

from kivy.graphics import Color, Rectangle
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.uix.widget import Widget
from pathlib import Path

from databaseManagers import Database as db
from sqlite3 import IntegrityError
DEFAULT_SYSTEM_FILE = "/home/student/PycharmProjects/elory"  # str(Path.home())     # Where system view opens by default
# TODO Have consistency across database and system views in respect to tagged files -> a selected file on system view
#   should still reflect its tags. (Will possibly have to tweak FileChooser classes -> just the FileListEntry template)


class FileNavigationPane(RelativeLayout):
    active_selected_file = ObjectProperty()         # TODO This property really belongs in the displayFilePane

    def __init__(self, **kwargs):
        super(FileNavigationPane, self).__init__(**kwargs)
        # self.bind(active_selected_file=throwaway)
        # Top Level View Options
        self.add_widget(Label(text="File Navigator", size_hint=(1, 0.06), size_hint_max_y=35, pos_hint={"top": 1}))
        view_options = BoxLayout(size_hint=(1, 0.06), pos_hint={"top": 0.94}, orientation='horizontal')
        view_options.add_widget(ToggleButton(text="System Files", group="view_options", state='down', on_press=self.set_system_file_view))
        view_options.add_widget(ToggleButton(text="Database Files", group="view_options", on_press=self.set_database_file_view))
        self.add_widget(view_options)

        # System Files Tree View    -> Roll own, instead of using FileChooser
        # sys_box = RelativeLayout(size_hint=(1, 0.85), pos_hint={"top": 0.85})
        # sys_box.add_widget(Button(text="Select folder..", size_hint=(0.4, 0.08), pos_hint={"top": 1}, on_press=self.select_folder,))
        # self.sys_tree = TreeView(root_options={"text": "System Files", "no_selection": True}, size_hint=(1, None))
        # self.sys_tree.bind(minimum_height=self.sys_tree.setter('height'))  # Auto update on height change
        # sys_viewport = ScrollView(pos_hint={"top": 0.9}, do_scroll_x=False, size_hint_y=0.79, scroll_type=["bars"])
        # sys_viewport.add_widget(self.sys_tree)
        # sys_box.add_widget(sys_viewport)
        # self.system_files_view = sys_box
        self.system_files_view = FileChooserListView(size_hint=(1, 0.84), pos_hint={"top": 0.85},
                                                     path=DEFAULT_SYSTEM_FILE, on_submit=self.add_system_file_to_db)
        self.system_files_view.bind(selection=self.set_active_file_object)
        # self.current_system_file_nodes = dict()  # TODO not used currently

        # Database Files Tree View
        db_box = RelativeLayout(size_hint=(1, 0.85), pos_hint={"top": 0.85})
        self.db_tree = DatabaseTree(root_options={"text": "Database Files", "no_selection": True},
                                    size_hint=(1, None),
                                    indent_level=10)
        self.db_tree.bind(minimum_height=self.db_tree.setter('height'))  # Auto update on height change
        db_box.add_widget(Button(text="Remove file", size_hint=(0.4, 0.06),
                                 pos_hint={"top": 1, "right": 0.45}, on_press=self.remove_file_from_db))
        file_options = BoxLayout(size_hint=(0.5, 0.06), pos_hint={"top": 1, "right": 1}, orientation='horizontal')
        file_options.add_widget(Label(text="Sort by : ", size_hint=(0.4, 1)))
        file_options.add_widget(Button(text="Folders", size_hint=(0.3, 1)))  # , on_press=self.db_tree.sort_by_folder))
        file_options.add_widget(Button(text="Tags", size_hint=(0.3, 1)))  # , on_press=self.db_tree.sort_by_tags))
        db_box.add_widget(file_options)

        db_viewport = ScrollView(pos_hint={"top": 0.92}, do_scroll_x=False, size_hint_y=0.79, scroll_type=["bars"])
        db_viewport.add_widget(self.db_tree)
        db_box.add_widget(db_viewport)
        self.database_files_view = db_box
        self.db_tree.bind(selected_node=self.set_active_file_object)

        # Init db Tree
        for file in db.FileManager.files.values():
            self.db_tree.add_file_node(file.path, file)

        self.add_widget(self.system_files_view)  # Start default view on System Files Pane

    def add_system_file_to_db(self, *args):
        # with dir_select to False, this should always only pass in files
        file_path = args[1][0]
        try:
            new_file = db.FileManager.add_file(file_path)   # Create new file in database -> this may throw errors
        except IntegrityError as errmsg:
            print(errmsg)
            print("Cannot add this file to database")
            return
        self.db_tree.add_file_node(file_path, new_file)

    def remove_file_from_db(self, *args):
        if self.db_tree.selected_node is None:
            return
        self.db_tree.remove_file_node(self.db_tree.selected_node)

    def set_active_file_object(self, *args):
        if type(args[0]) == FileChooserListView:   # Handle when MyFileChooserListView calls the function
            # print("--call set system file view--")
            # pprint.pprint(args[0].__dict__)
            # for each in args[0].__dict__['_items']:
            #     print()
            #     pprint.pprint(each.__dict__)
            #     if each.__dict__['selected']:
            #         print("-------------------------------------")
            #         pprint.pprint(each.__dict__['_proxy_ref'].__dict__)
            #         print("-------------------------------------")
            if args[1] == []:   # Passes empty list when dir select is False
                return
            path_string = args[1][0]
            # Create 'anon' object on the fly with 'path' member
            # This is a workaround. Ideally we could have a single object represent a file, regardless if it was in
            # the database
            self.active_selected_file = type('anon', (object, ), {"path": path_string})   # Pass 'anon' object
        if type(args[0]) == DatabaseTree:
            self.active_selected_file = args[1].db_object   # Pass db object itself

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

    def __init__(self, db_object, **kwargs):
        super(FileNode, self).__init__(**kwargs)
        self.db_object = db_object
        self.orientation = "horizontal"
        self.height = 28        # Default TreeNode size is 28

        descript = Label(text=self.db_object.name, halign="left", valign="center")
        descript.bind(size=descript.setter("text_size"))
        self.add_widget(descript)


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
