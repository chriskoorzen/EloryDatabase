from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.treeview import TreeView, TreeViewNode

from modals import UserInputBox, SelectFromList, Notification
from databaseObjects import TagGroup

import logging
tagpane_logger = logging.getLogger(__name__)
tagpane_logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(fmt)
tagpane_logger.addHandler(handler)
tagpane_logger.propagate = False


class TagPane(RelativeLayout):
    add_tag_func = ObjectProperty()             # references file display "add_new_tag" func

    db = ObjectProperty()
    groups = ObjectProperty()
    tags = ObjectProperty()

    def __init__(self, **kwargs):
        super(TagPane, self).__init__(**kwargs)

    def on_kv_post(self, base_widget):
        pass

    def on_parent(self, *args):
        pass

    def load_objects(self):
        # Clear previous nodes
        self.ids["tree_root"].clear_all_nodes()

        # Load View objects
        for item in self.groups.values():
            group_node = GroupNode(db_object=item, add_tag_func=self.add_tag, del_tag_func=self.delete_tag)
            self.ids["tree_root"].add_node(group_node)
            for child_id in item.tags:
                child = self.tags[child_id]
                tag_node = TagNode(db_object=child, on_double_press=self.add_tag_func)
                self.ids["tree_root"].add_node(tag_node, parent=group_node)
            self.ids["tree_root"].toggle_node(group_node)      # Let default view be open nodes
        tagpane_logger.info("GUI objects initialized..")

    # CRUD
    def add_group(self):

        def add(*args):
            new_name = args[1][0]
            success, new_group = TagGroup.new_group(self.db, new_name)
            if not success:
                message = "Unknown error"
                if str(new_group) == "UNIQUE constraint failed: tag_groups.group_name":
                    message = f"The Group name '{new_name}' already exists. Please choose another."
                n = Notification(heading="Error", info=message)
                n.open()
                tagpane_logger.warning("Input error: " + message)
                return

            # Update Model
            self.groups[new_group.name] = new_group
            # Update View
            group_node = GroupNode(db_object=new_group, add_tag_func=self.add_tag, del_tag_func=self.delete_tag)
            self.ids["tree_root"].add_node(group_node)
            tagpane_logger.info("New GroupNode added to view")

        heading = "Add New Group"
        info = "New Group name.\n\nGroup names must be unique."
        text_descript = ".. new name .."
        d = UserInputBox(heading=heading, info=info, text_descript=text_descript, submit_call=add)
        d.open()

    def rename_group(self):
        pass

    def delete_group(self):      # TODO prevent the deletion of a group if even one tag has links?

        def delete(*args):
            name = args[1][0]
            group = self.groups[name]
            if not group.delete(self.db):
                tagpane_logger.warning("Error deleting group node")
                message = "Cannot delete groups with tags. " \
                          "First remove files from tags, then tags from groups, and try again."
                n = Notification(heading="Error", info=message)
                n.open()
                return
            # Update Model
            del self.groups[name]
            # Update View
            for node in self.ids["tree_root"].iterate_all_nodes():
                if node.text == name:
                    self.ids["tree_root"].remove_node(node)
                    break
            tagpane_logger.info("Successfully deleted group node")

        heading = "Delete Group"
        list_heading = ""
        d = SelectFromList(heading=heading, list_heading=list_heading,
                           item_list=[x for x in self.groups.keys()],
                           submit_call=delete)
        d.open()

    def add_tag(self, group_node):       # TODO partition out the "add new Tag node" and "create new Tag" functions
        # For use with the GroupNode button

        def add(*args):
            success, new_tag = group_node.db_object.create_tag(self.db, *args[1])
            if not success:
                message = "Unknown error"
                if str(new_tag) == "UNIQUE constraint failed: tags.tag_name, tags.tag_group":
                    message = f"The Tag name '{args[1]}' already exists within Group '{group_node.db_object.name}'. " \
                              f"Please choose another."
                n = Notification(heading="Error", info=message)
                n.open()
                tagpane_logger.warning("Error creating tag node: " + message)
                return
            # Update Model
            self.tags[new_tag.db_id] = new_tag
            # Update View
            self.ids["tree_root"].add_node(TagNode(new_tag, on_double_press=self.add_tag_func), parent=group_node)
            tagpane_logger.info("Successfully created tag node")

        heading = f"Create New Tag for Group {group_node.text}"
        info = "New Tag name\n\nTag names must be unique within their Group."
        text_descript = ".. new Tag name .."
        d = UserInputBox(heading=heading, info=info, text_descript=text_descript, submit_call=add)
        d.open()

    def rename_tag(self):
        pass

    def delete_tag(self):   # TODO should pass group node
        # For use with the GroupNode button
        current_node = self.ids["tree_root"].selected_node
        if current_node is None:
            return
        success = current_node.db_object.group.delete_tag(self.db, current_node.db_object)
        if not success:
            tagpane_logger.warning("Error deleting tag node")
            message = "Cannot delete tags linked to files. Unlink all files from this tag and try again."
            n = Notification(heading="Error", info=message)
            n.open()
            return
        # Update Model
        del self.tags[current_node.db_object.db_id]
        # Update View
        self.ids["tree_root"].remove_node(current_node)
        tagpane_logger.info("Successfully deleted tag node")


class GroupNode(TreeViewNode, BoxLayout):
    text = StringProperty()

    def __init__(self, db_object, add_tag_func, del_tag_func, **kwargs):
        super(GroupNode, self).__init__(**kwargs)
        self.db_object = db_object
        self.add_tag_func = add_tag_func
        self.del_tag_func = del_tag_func
        self.text = self.db_object.name


class TagNode(TreeViewNode, BoxLayout):
    text = StringProperty()

    def __init__(self, db_object, **kwargs):
        super(TagNode, self).__init__(**kwargs)
        # Implement Double Click functionality
        self.register_event_type('on_double_press')
        if kwargs.get("on_double_press") is not None:
            self.bind(on_double_press=kwargs.get("on_double_press"))

        self.db_object = db_object
        self.text = self.db_object.name

    # Implement Double Click functionality
    def on_touch_down(self, touch):
        if touch.is_double_tap:
            self.dispatch('on_double_press', touch)
            return True     # return True to stop dispatching, False to propagate
        return BoxLayout.on_touch_down(self, touch)

    # Implement Double Click functionality
    def on_double_press(self, *args):
        pass


class RecycleTree(TreeView):

    def __init__(self, **kwargs):
        super(RecycleTree, self).__init__(**kwargs)

    def clear_all_nodes(self):
        for node in [x for x in self.iterate_all_nodes()]:
            self.remove_node(node)
        tagpane_logger.info("All nodes cleared..")
