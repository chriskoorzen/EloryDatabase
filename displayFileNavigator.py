import os
from collections import deque

from kivy.graphics import Color, Rectangle
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
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


class FileNavigationPane(RelativeLayout):
    active_selected_file = StringProperty()

    def __init__(self, **kwargs):
        super(FileNavigationPane, self).__init__(**kwargs)
        # self.bind(active_selected_file=throwaway)
        # Top Level View Options
        self.add_widget(Label(text="File Navigator", size_hint=(1, 0.08), pos_hint={"top": 1}))
        view_options = BoxLayout(size_hint=(1, 0.06), pos_hint={"top": 0.92}, orientation='horizontal')
        view_options.add_widget(ToggleButton(text="System Files", group="view_options", state='down', on_press=self.set_system_file_view))
        view_options.add_widget(ToggleButton(text="Database Files", group="view_options", on_press=self.set_database_file_view))
        self.add_widget(view_options)

        # System Files Tree View
        # sys_box = RelativeLayout(size_hint=(1, 0.85), pos_hint={"top": 0.85})
        # sys_box.add_widget(Button(text="Select folder..", size_hint=(0.4, 0.08), pos_hint={"top": 1}, on_press=self.select_folder,))
        # self.sys_tree = TreeView(root_options={"text": "System Files", "no_selection": True}, size_hint=(1, None))
        # self.sys_tree.bind(minimum_height=self.sys_tree.setter('height'))  # Auto update on height change
        # sys_viewport = ScrollView(pos_hint={"top": 0.9}, do_scroll_x=False, size_hint_y=0.79, scroll_type=["bars"])
        # sys_viewport.add_widget(self.sys_tree)
        # sys_box.add_widget(sys_viewport)
        # self.system_files_view = sys_box
        self.system_files_view = FileChooserListView(size_hint=(1, 0.84), pos_hint={"top": 0.85}, path=str(Path.home()))
        self.system_files_view.bind(selection=self.set_active_image)

        # Database Files Tree View
        db_box = RelativeLayout(size_hint=(1, 0.85), pos_hint={"top": 0.85})
        sort_options = BoxLayout(size_hint=(1, 0.08), pos_hint={"top": 1}, orientation='horizontal')
        sort_options.add_widget(Label(text="Sort by : ", size_hint=(0.4, 1)))
        sort_options.add_widget(Button(text="Folders", size_hint=(0.3, 1)))         # Let db_tree display by folder
        sort_options.add_widget(Button(text="Tags", size_hint=(0.3, 1)))            # Let db_tree display by tag
        db_box.add_widget(sort_options)
        self.db_tree = TreeView(root_options={"text": "Database Files", "no_selection": True}, size_hint=(1, None))
        self.db_tree.bind(minimum_height=self.db_tree.setter('height'))  # Auto update on height change
        db_viewport = ScrollView(pos_hint={"top": 0.9}, do_scroll_x=False, size_hint_y=0.79, scroll_type=["bars"])
        db_viewport.add_widget(self.db_tree)
        db_box.add_widget(db_viewport)
        self.database_files_view = db_box
        self.db_tree.bind(selected_node=self.set_active_image)

        self.add_widget(self.system_files_view)     # Set default view on System Files Pane

        self.database_file_nodes = dict()
        self.current_system_file_nodes = dict()

        self._init_db_tree(list(self._parse_db_files().items()))
        # a = TreeViewLabel(text="My_name")
        # b = TreeViewLabel(text="My_name")
        # print(a==b)   # False  -> implement own __eq__ method in class. __hash__

    def set_active_image(self, *args):
        if type(args[0]) == FileChooserListView:
            self.active_selected_file = args[1][0]
        if type(args[0]) == TreeView:
            self.active_selected_file = args[1].db_object.path

    def set_system_file_view(self, *args):
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

    def select_folder(self, *args):

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

    def _init_db_tree(self, list_structure_dict, parent=None):

        for key, value in list_structure_dict:
            if isinstance(value, type({})):
                dir_label = TreeViewLabel(text=key, no_selection=True)
                self.db_tree.add_node(dir_label, parent=parent)
                self.db_tree.toggle_node(dir_label)
                return self._init_db_tree(list(value.items()), dir_label)
            else:
                file_node = FileNode(value)
                self.db_tree.add_node(file_node, parent=parent)
                self.database_file_nodes[file_node.db_object.path] = file_node

    def _parse_db_files(self):
        """return a dictionary of the directory layout structure"""
        def directory_builder(path_deque, base_dict, obj):
            if len(path_deque) == 1:
                base_dict[path_deque.popleft()] = obj
                return
            else:
                key = path_deque.popleft()
                if key in base_dict:
                    return directory_builder(path_deque, base_dict[key], obj)
                else:
                    new_dict = {}
                    base_dict[key] = new_dict
                    return directory_builder(path_deque, new_dict, obj)

        file_dict = {}
        for file in db.FileManager.files.values():
            path = deque(file.path.split(os.sep))
            if path[0] == '':       # For Unix
                path.popleft()      # Remove '/' root
            directory_builder(path, file_dict, file)
        return file_dict


class FileNode(TreeViewNode, BoxLayout):

    def __init__(self, db_object, **kwargs):
        super(FileNode, self).__init__(**kwargs)
        self.db_object = db_object
        self.orientation = "horizontal"
        self.height = 28        # Default TreeNode size is 28

        descript = Label(text=self.db_object.name, halign="left", valign="center")
        descript.bind(size=descript.setter("text_size"))
        self.add_widget(descript)


def throwaway(*args):
    print("function executed", *args)
