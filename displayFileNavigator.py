import pprint
import gc
import os

from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import NoTransition
from kivy.uix.treeview import TreeViewLabel, TreeViewNode
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior

from databaseObjects import File
from displayTagPane import RecycleTree
from modals import Notification

import logging
filenav_logger = logging.getLogger(__name__)
filenav_logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(fmt)
filenav_logger.addHandler(handler)
filenav_logger.propagate = False


class FileNavigationPane(RelativeLayout):
    db = ObjectProperty()
    files = ObjectProperty()
    groups = ObjectProperty()
    tags = ObjectProperty()

    active_selected_file = ObjectProperty()
    system_view_path = StringProperty()

    def __init__(self, **kwargs):
        super(FileNavigationPane, self).__init__(**kwargs)

    def load_objects(self):
        self.sort_by_tags()
        # self.ids["default_view"].dispatch("on_press")     # FIXME if fail to open other db, this acts weird
        self.ids["default_view"].state = "down"
        self.ids["other_view"].state = "normal"
        # self.ids["default_sort"].dispatch("on_press")
        self.ids["default_sort"].state = "down"
        self.ids["other_sort"].state = "normal"
        filenav_logger.info("File objects initialized..")

    def on_kv_post(self, base_widget):
        self.ids["view_manager"].transition = NoTransition()
        self.ids["view_manager"].current = "database_files"
        filenav_logger.info("Set default view on 'database files'...")

    def change_system_view_path(self, new_path):
        self.system_view_path = new_path

    def refresh_view(self):
        t = ToggleButtonBehavior.get_widgets("sort_options")
        for btn in t:
            if btn.state == "down":
                btn.dispatch("on_press")

    def sort_by_folder(self, *args):
        self.ids["db_tree"].clear_all_nodes()
        self.ids["db_tree"].indent_level = 18
        for file in self.files.values():
            self.ids["db_tree"].add_file_node(file.path, file)
        filenav_logger.info("Sort by folders...")

    def sort_by_tags(self, *args):
        self.ids["db_tree"].clear_all_nodes()
        self.ids["db_tree"].indent_level = 20
        # TODO better method
        untagged = TreeViewLabel(text="Untagged Files", no_selection=True)
        self.ids["db_tree"].add_node(untagged)
        self.ids["db_tree"].toggle_node(untagged)
        for file in self.files.values():
            if not file.tags:
                file_node = FileNode(file, no_selection=False)
                self.ids["db_tree"].add_node(file_node, parent=untagged)
        # Only add Groups and Tags of tagged files - avoid adding empty tags
        for group in self.groups.values():
            if group.has_files():
                g_node = TreeViewLabel(text=group.name, no_selection=True)
                self.ids["db_tree"].add_node(g_node)
                self.ids["db_tree"].toggle_node(g_node)                                 # Toggle Groups open
                for tag in group.tags.values():
                    if tag.files:
                        t_node = TreeViewLabel(text=tag.name, no_selection=True)
                        self.ids["db_tree"].add_node(t_node, parent=g_node)
                        # self.ids["db_tree"].toggle_node(t_node)                         # Toggle Tags open
                        for file in tag.files:
                            f_node = FileNode(self.files[file], no_selection=False)
                            self.ids["db_tree"].add_node(f_node, parent=t_node)
        filenav_logger.info("Sort by tags...")

    def add_system_file_to_db(self, *args):
        # with dir_select to False, this should always only pass in files
        # Execute on System File View, doubleclick on file
        if not len(args[0]):       # Doubleclick on folder will return empty list of args
            return
        success, new_file = File.new_file(args[0][0], self.db)
        if not success:
            filenav_logger.warning(new_file)
            n = Notification(heading="Error", info=str(new_file))
            n.open()
            return
        # Update Model
        self.files[new_file.path] = new_file
        # Update View
        self.refresh_view()
        filenav_logger.info("New file node created")

    def remove_file_from_db(self, *args):
        if args[0] is None:
            return
        # args[0] is a Widget with reference to the underlying object
        success = args[0].db_object.delete(self.db)
        if not success[0]:
            message = success[1]
            n = Notification(heading="Error", info=message)
            n.open()
            filenav_logger.warning("Failed file node deletion")
            return
        # Remove from Model
        del self.files[args[0].db_object.path]
        # Remove from View
        self.ids["db_tree"].remove_node(args[0])
        filenav_logger.info("Successfully deleted file node")

    def set_active_file_object(self, selection):
        if type(selection) == FileNode:
            self.active_selected_file = selection.db_object.path
            return
        if selection == []:
            return
        self.active_selected_file = selection[0]


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
        filenav_logger.info("Cleared all database nodes...")

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
