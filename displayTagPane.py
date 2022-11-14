from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import DictProperty
from kivy.uix.treeview import TreeView, TreeViewLabel

from databaseManagers import Database as db


class TagPane(RelativeLayout):
    tags = DictProperty()       # Not used so far
    groups = DictProperty()

    def __init__(self, **kwargs):
        super(RelativeLayout, self).__init__(**kwargs)
        self.set_data()
        self.tree_root = TreeView(root_options={"text": "File Tags", "no_selection": True})
        self.update_treeview()

    def set_data(self):
        self.tags = db.TagManager.tags
        self.groups = db.TagManager.groups

    def update_treeview(self):
        # Only adds all items once
        def test_print(*args):
            print(*args)
            print("Double Clicked")
        for item in self.groups.values():
            group_node = TreeViewLabel(text=item.name)
            self.tree_root.add_node(group_node)
            for child in item.tags.values():
                tag_node = TreeViewLabel(text=child.name, on_touch_down=test_print)
                self.tree_root.add_node(tag_node, parent=group_node)

        self.add_widget(self.tree_root)

# TODO create custom tag label class -> register double clicks
# TODO create custom group label class -> tiny buttons to add and remove tags
