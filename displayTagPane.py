from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import DictProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.treeview import TreeView, TreeViewNode

from databaseManagers import Database as db


class TagPane(RelativeLayout):

    def __init__(self, **kwargs):
        super(RelativeLayout, self).__init__(**kwargs)
        # Create Layout
        self.add_widget(Label(text="Tag Manager", size_hint=(1, 0.08), pos_hint={"top": 1}))
        options_box = BoxLayout(pos_hint={"top": 0.92}, size_hint=(1, 0.06), orientation="horizontal")
        options_box.add_widget(Button(text="Add New Group"))
        options_box.add_widget(Button(text="Delete Group"))
        options_box.add_widget(Button(text="Delete Tag"))
        self.add_widget(options_box)

        self.tree_root = TreeView(root_options={"text": "File Tags", "no_selection": True},
                                  size_hint=(1, None))
        self.tree_root.bind(minimum_height=self.tree_root.setter('height'))     # Auto update on height change
        # self.tree_height = self.tree_root.minimum_height
        viewport = ScrollView(pos_hint={"top": 0.85}, do_scroll_x=False, size_hint_y=0.79, scroll_type=["bars"])
        viewport.add_widget(self.tree_root)
        self.add_widget(viewport)

        # Populate TreeView
        self.init_treeview()

    def init_treeview(self):
        # Only adds all items once
        for item in db.TagManager.groups.values():
            group_node = GroupNode(db_object=item, add_tag_func=self.add_tag)
            self.tree_root.add_node(group_node)
            for child in item.tags.values():
                tag_node = TagNode(db_object=child, on_double_press=self.test_print)
                self.tree_root.add_node(tag_node, parent=group_node)
            self.tree_root.toggle_node(group_node)      # Let default view be open nodes

    def test_print(*args):
        print(args[0])
        print("Double Clicked")

    def add_group(self):
        pass

    def rename_group(self):
        pass

    def delete_group(self):
        pass

    def add_tag(self, *args):
        # For use with the GroupNode button
        db_obj = args[0].parent.db_object
        parent_node = args[0].parent

        def get_text_and_update(*arg):
            new_tag = db.TagManager.new_tag(user_input.text, db_obj)
            self.tree_root.add_node(
                TagNode(db_object=new_tag, on_double_press=self.test_print),
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
        popup = Popup(title=f'Create New Tag for Group "{db_obj.name}"',
                      content=contentBox,
                      size_hint=(None, None),
                      size=(300, 200))
        cancelBtn.bind(on_press=popup.dismiss)
        acceptBtn.bind(on_press=get_text_and_update)
        acceptBtn.bind(on_release=popup.dismiss)
        popup.open()

    def rename_tag(self):
        pass

    def delete_tag(self):
        pass


# TODO create custom group label class -> tiny buttons to add and remove tags
class GroupNode(TreeViewNode, BoxLayout):

    def __init__(self, db_object, add_tag_func, **kwargs):
        super(BoxLayout, self).__init__(**kwargs)
        self.db_object = db_object
        self.orientation = "horizontal"
        self.height = 36        # Default TreeNode size is 28
        descript = Label(text=self.db_object.name, halign="left", valign="center")
        descript.bind(size=descript.setter("text_size"))
        self.add_widget(descript)

        self.add_widget(Button(text="+ tag", on_press=add_tag_func, size_hint_x=0.2))
        super(TreeViewNode, self).__init__(**kwargs)


# TODO create custom tag label class -> register double clicks
class TagNode(TreeViewNode, BoxLayout):

    def __init__(self, db_object, **kwargs):
        super(BoxLayout, self).__init__(**kwargs)
        # Implement Double Click functionality
        self.register_event_type('on_double_press')
        if kwargs.get("on_double_press") is not None:
            self.bind(on_double_press=kwargs.get("on_double_press"))

        self.db_object = db_object
        self.orientation = "horizontal"
        self.height = 28        # Default TreeNode size is 28
        descript = Label(text=self.db_object.name, halign="left", valign="center")
        descript.bind(size=descript.setter("text_size"))
        self.add_widget(descript)

        super(TreeViewNode, self).__init__(**kwargs)

    # Implement Double Click functionality
    def on_touch_down(self, touch):
        if touch.is_double_tap:
            self.dispatch('on_double_press', touch)
            return True
        return BoxLayout.on_touch_down(self, touch)

    # Implement Double Click functionality
    def on_double_press(self, *args):
        pass

