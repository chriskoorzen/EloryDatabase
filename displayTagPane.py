from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.textinput import TextInput
from kivy.uix.treeview import TreeView, TreeViewNode, TreeViewLabel

from sqlite3 import IntegrityError
from databaseManagers import Database as db


class TagPane(RelativeLayout):
    selected_tag = ObjectProperty()

    def __init__(self, **kwargs):
        super(TagPane, self).__init__(**kwargs)

    def init_treeview(self):
        # Only adds all items once
        for item in db.TagManager.groups.values():
            group_node = GroupNode(db_object=item, add_tag_func=self.add_tag, del_tag_func=self.delete_tag)
            self.ids["tree_root"].add_node(group_node)
            for child in item.tags.values():
                tag_node = TagNode(db_object=child, on_double_press=self.set_selected_tag)
                self.ids["tree_root"].add_node(tag_node, parent=group_node)
            self.ids["tree_root"].toggle_node(group_node)      # Let default view be open nodes

    def set_selected_tag(self, *args):
        # First arg is TagNode object
        # print(*args)
        # print("Double Clicked")
        self.selected_tag = args[0]

    def add_group(self, *args):

        def get_text_and_update(*arg):
            try:
                new_group = db.TagManager.new_group(user_input.text)
            except IntegrityError:
                errmsg = Label(
                    text="Invalid name.\nGroup names cannot be empty, must be alphanumeric characters\nand must be unique.")
                popup = Popup(title="Error",
                              content=errmsg,
                              size_hint=(None, None),
                              size=(600, 200))
                popup.open()
                return
            self.ids["tree_root"].add_node(
                GroupNode(db_object=new_group, add_tag_func=self.add_tag, del_tag_func=self.delete_tag)
            )

        user_input = TextInput(hint_text="New group name...", multiline=False)
        acceptBtn = Button(text="Submit")
        cancelBtn = Button(text="Cancel")
        btnBox = BoxLayout(orientation="horizontal")
        btnBox.add_widget(cancelBtn)
        btnBox.add_widget(acceptBtn)
        contentBox = BoxLayout(orientation="vertical")
        contentBox.add_widget(user_input)
        contentBox.add_widget(btnBox)
        popup = Popup(title='Create New Group',
                      content=contentBox,
                      size_hint=(None, None),
                      size=(300, 200))
        cancelBtn.bind(on_press=popup.dismiss)
        acceptBtn.bind(on_press=get_text_and_update)
        acceptBtn.bind(on_release=popup.dismiss)
        popup.open()

    def rename_group(self):
        pass

    def delete_group(self, *args):      # TODO prevent the deletion of a group if even one tag has links?

        def get_selection_and_del(*arg):
            if del_options.selected_node is None:       # TODO Catch None type error
                return True
            group_node, group = reference[del_options.selected_node.ids["db_id"]]
            tag_nodes = [x for x in group_node.nodes]
            for tag_node in tag_nodes:
                try:
                    db.TagManager.delete_tag(tag_node.db_object.db_id)
                    self.ids["tree_root"].remove_node(tag_node)
                except IntegrityError:
                    errmsg = Label(
                        text="Cannot delete tags attached to files.\nRemove tag from all files and try again\n")
                    popup = Popup(title="Error",
                                  content=errmsg,
                                  size_hint=(None, None),
                                  size=(600, 200))
                    popup.open()
                    return
            db.TagManager.delete_group(group.db_id)
            self.ids["tree_root"].remove_node(group_node)

        del_options = TreeView(root_options={"text": "Tag Groups", "no_selection": True})
        reference = {}
        for node in self.ids["tree_root"].root.nodes:
            item = node.db_object
            reference[item.db_id] = [node, item]
            file_count = 0
            for tag in item.tags.values():
                file_count += len(tag.files)
            del_options.add_node(TreeViewLabel(text=f"{item.name}  ({len(item.tags)}) - {file_count} linked files",
                                               ids={"db_id": item.db_id}))
        acceptBtn = Button(text="Submit")
        cancelBtn = Button(text="Cancel")
        btnBox = BoxLayout(orientation="horizontal", size_hint=(1, 0.3))
        btnBox.add_widget(cancelBtn)
        btnBox.add_widget(acceptBtn)
        contentBox = BoxLayout(orientation="vertical")
        contentBox.add_widget(del_options)
        contentBox.add_widget(btnBox)
        popup = Popup(title='Delete Group',
                      content=contentBox,
                      size_hint=(None, None),
                      size=(400, 350))
        cancelBtn.bind(on_press=popup.dismiss)
        acceptBtn.bind(on_press=get_selection_and_del)
        acceptBtn.bind(on_release=popup.dismiss)
        popup.open()

    def add_tag(self, *args):       # TODO partition out the "add new Tag node" and "create new Tag" functions
        # For use with the GroupNode button
        db_obj_group = args[0].db_object
        parent_node = args[0]

        def get_text_and_update(*arg):
            try:
                new_tag = db.TagManager.new_tag(user_input.text, db_obj_group)
            except IntegrityError:
                errmsg = Label(text="Invalid name.\nTag names cannot be empty, must be alphanumeric characters only\n and be unique within a Group")
                popup = Popup(title="Error",
                              content=errmsg,
                              size_hint=(None, None),
                              size=(600, 200))
                popup.open()
                return
            self.ids["tree_root"].add_node(
                TagNode(db_object=new_tag, on_double_press=self.set_selected_tag),
                parent_node
            )
        user_input = TextInput(hint_text="Your tag name here", multiline=False)
        acceptBtn = Button(text="Submit")
        cancelBtn = Button(text="Cancel")
        btnBox = BoxLayout(orientation="horizontal")
        btnBox.add_widget(cancelBtn)
        btnBox.add_widget(acceptBtn)
        contentBox = BoxLayout(orientation="vertical")
        contentBox.add_widget(user_input)
        contentBox.add_widget(btnBox)
        popup = Popup(title=f'Create New Tag for Group "{db_obj_group.name}"',
                      content=contentBox,
                      size_hint=(None, None),
                      size=(300, 200))
        cancelBtn.bind(on_press=popup.dismiss)
        acceptBtn.bind(on_press=get_text_and_update)
        acceptBtn.bind(on_release=popup.dismiss)
        popup.open()

    def rename_tag(self):
        pass

    def delete_tag(self, *args):
        # For use with the GroupNode button
        current_node = self.ids["tree_root"].selected_node
        if current_node is None:
            return
        try:
            db.TagManager.delete_tag(current_node.db_object.db_id)
        except IntegrityError:
            errmsg = Label(
                text="Cannot delete tags attached to files.\nRemove tag from all files and try again")
            popup = Popup(title="Error",
                          content=errmsg,
                          size_hint=(None, None),
                          size=(600, 200))
            popup.open()
            return
        self.ids["tree_root"].remove_node(current_node)


# TODO create custom group label class -> tiny buttons to add and remove tags
class GroupNode(TreeViewNode, BoxLayout):
    display_name = StringProperty()

    def __init__(self, db_object, add_tag_func, del_tag_func, **kwargs):
        super(GroupNode, self).__init__(**kwargs)
        self.db_object = db_object
        self.add_tag_func = add_tag_func
        self.del_tag_func = del_tag_func
        self.display_name = self.db_object.name


# TODO create custom tag label class -> register double clicks
class TagNode(TreeViewNode, BoxLayout):
    display_name = StringProperty()

    def __init__(self, db_object, **kwargs):
        super(TagNode, self).__init__(**kwargs)
        # Implement Double Click functionality
        self.register_event_type('on_double_press')
        if kwargs.get("on_double_press") is not None:
            self.bind(on_double_press=kwargs.get("on_double_press"))

        self.db_object = db_object
        self.display_name = self.db_object.name

    # Implement Double Click functionality
    def on_touch_down(self, touch):
        if touch.is_double_tap:
            self.dispatch('on_double_press', touch)
            return True     # return True to stop dispatching, False to propagate
        return BoxLayout.on_touch_down(self, touch)

    # Implement Double Click functionality
    def on_double_press(self, *args):
        pass

