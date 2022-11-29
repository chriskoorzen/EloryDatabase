import pprint
import gc
import os

from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import NoTransition
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from pathlib import Path

from sqlite3 import IntegrityError

from databaseObjects import File
from displayTagPane import RecycleTree


# TODO Have consistency across database and system views in respect to tagged files -> a selected file on system view
#   should still reflect its tags. (Will possibly have to tweak FileChooser classes -> just the FileListEntry template)


class FileNavigationPane(RelativeLayout):
    db = ObjectProperty()
    files = ObjectProperty()
    groups = ObjectProperty()
    tags = ObjectProperty()

    active_selected_file = ObjectProperty()
    system_view_path = StringProperty()

    def __init__(self, **kwargs):
        super(FileNavigationPane, self).__init__(**kwargs)
        # print("FileNavigationPane init")
        # print("FileNavigationPane db:", hex(id(self.db)))
        # print("FileNavigationPane files:", hex(id(self.files)))
        # print("FileNavigationPane groups:", hex(id(self.groups)))
        # print("FileNavigationPane tags:", hex(id(self.tags)))

    def load_objects(self):
        self.sort_by_tags()
        self.ids["default_view"].state = "down"
        self.ids["default_sort"].state = "down"

    def on_kv_post(self, base_widget):
        self.ids["view_manager"].transition = NoTransition()
        self.ids["view_manager"].current = "database_files"
        # print("FileNavigationPane on_kv_post")
        # print("FileNavigationPane db:", hex(id(self.db)))
        # print("FileNavigationPane files:", hex(id(self.files)))
        # print("FileNavigationPane groups:", hex(id(self.groups)))
        # print("FileNavigationPane tags:", hex(id(self.tags)))

    def change_system_view_path(self, new_path):
        self.system_view_path = new_path

    def sort_by_folder(self, *args):
        self.ids["db_tree"].clear_all_nodes()
        self.ids["db_tree"].indent_level = 10
        for file in self.files.values():
            self.ids["db_tree"].add_file_node(file.path, file)

    def sort_by_tags(self, *args):
        self.ids["db_tree"].clear_all_nodes()
        self.ids["db_tree"].indent_level = 20
        # TODO better method
        untagged = TreeViewLabel(text="Untagged Files", no_selection=True)
        self.ids["db_tree"].add_node(untagged)
        self.ids["db_tree"].toggle_node(untagged)
        display = {}        # Only add Groups and Tags of tagged files - avoid adding empty tags
        for file in self.files.values():
            if not file.tags:
                file_node = FileNode(file, no_selection=False)
                self.ids["db_tree"].add_node(file_node, parent=untagged)
        for tag in self.tags.values():
            if not tag.files:
                continue
            if tag.group not in display:
                display[tag.group] = [tag]
            else:
                display[tag.group].append(tag)
        for group in display.keys():
            g_node = TreeViewLabel(text=self.groups[group].name, no_selection=True)
            self.ids["db_tree"].add_node(g_node)
            self.ids["db_tree"].toggle_node(g_node)
            for tag in display[group]:
                t_node = TreeViewLabel(text=tag.name, no_selection=True)
                self.ids["db_tree"].add_node(t_node, parent=g_node)
                self.ids["db_tree"].toggle_node(t_node)
                for file in tag.files:
                    f_node = FileNode(self.files[file], no_selection=False)
                    self.ids["db_tree"].add_node(f_node, parent=t_node)

    def add_system_file_to_db(self, *args):
        # with dir_select to False, this should always only pass in files
        # Execute on System File View, doubleclick on file
        if not len(args[0]):       # Doubleclick on folder will return empty list of args
            return
        try:
            file_id, file_hash = self.db.create_entry("file", [{'file_path': args[0][0]}])[0]  # Expect a list with 1 tuple
        except IntegrityError as errmsg:
            print(errmsg)
            print("Cannot add this file to database")
            return
        # Update Model
        self.files[file_id] = File(file_id, args[0][0], file_hash)
        print("File Nav DB_files:", hex(id(self.files)))
        print("File Nav DB:", hex(id(self.db)))
        # Update View
        # Create new object for View -> since you have to be at System File View to execute this function, switching
        # back will automatically update the view
        # TODO unless the "sort" is not refreshed, it wont display

    def remove_file_from_db(self, *args):
        if args[0] is None:
            return
        try:
            success = self.db.delete_entry("file", [{'file_id': args[0].db_object.db_id}])[0]
        except IntegrityError as errmsg:
            print("Cannot delete tagged file", errmsg)
            return
        if not success:
            print("fail")
            return
        # Remove from Model
        del self.files[args[0].db_object.db_id]
        # Remove from View
        self.ids["db_tree"].remove_node(args[0])        # TODO won't auto update folder view

    def set_active_file_object(self, selection):
        if type(selection) == FileNode:
            self.active_selected_file = selection.db_object   # Pass db object itself
            return
        if selection == []:
            return
        # Create 'anon' object on the fly with 'path' member
        # This is a workaround. Ideally we could have a single object represent a file, regardless if it was in
        # the database
        # TODO just search if we have a matching path (although could break if files are moved) and pass the matching
        #   object, otherwise, pass anon object.
        self.active_selected_file = type('anon', (object,), {"path": selection[0], "tags": []})  # Pass 'anon' object


class FileNode(TreeViewNode, BoxLayout):
    display_name = StringProperty()

    def __init__(self, db_object, **kwargs):
        super(FileNode, self).__init__(**kwargs)
        self.db_object = db_object
        self.display_name = self.db_object.name


class DatabaseTree(RecycleTree):

    def __init__(self, **kwargs):
        super(DatabaseTree, self).__init__(**kwargs)
        self.directory_layout = {}    # Flat dict -> key: file_path (incl directories), value: node

    def clear_all_nodes(self):
        super(DatabaseTree, self).clear_all_nodes()
        self.directory_layout.clear()

    def add_file_node(self, file_path, file_obj):
        # A function that auto creates folder labels by from a given path
        path = file_path.split(os.sep)
        file_name = path.pop()
        full_dir = ''
        parent = None
        for directory in path:
            full_dir += (directory + os.sep)
            if full_dir not in self.directory_layout:                           # Directory does not exist
                dir_node = TreeViewLabel(text=directory, no_selection=True)     # Create node for directory
                self.directory_layout[full_dir] = dir_node              # Set reference between directory path and node
                super(DatabaseTree, self).add_node(dir_node, parent=parent)     # Add to tree
                self.toggle_node(dir_node)
                parent = dir_node                                   # Set node as parent for next folder in hierarchy
            else:                                                   # Directory already exists
                parent = self.directory_layout[full_dir]            # Set node as parent for next folder in hierarchy
        full_dir += file_name                                       # Get path for file
        file_node = FileNode(file_obj)                              # Create node for File
        self.directory_layout[full_dir] = file_node                 # Set reference between path and file
        super(DatabaseTree, self).add_node(file_node, parent=parent)    # Add to Tree

    def remove_file_node(self, file_node):
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
