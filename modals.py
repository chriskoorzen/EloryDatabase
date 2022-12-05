from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.treeview import TreeViewLabel


class DialogBox(Popup):     # Super class?

    def __init__(self, **kwargs):
        super(DialogBox, self).__init__(**kwargs)


class UserInputBox(Popup):
    user_input = StringProperty()

    def __init__(self, heading=None, info=None, text_descript=None, submit_call=None, validate_call=None, **kwargs):
        super(UserInputBox, self).__init__(**kwargs)

        self.title = heading if heading is not None else self.title
        self.ids["info"].text = info if info is not None else ""
        # self.ids["info"].pos_hint = {"top": 1 - self.ids["user_input"].pos_hint["top"]}
        self.ids["user_input"].hint_text = text_descript if text_descript is not None else ""

        if submit_call is not None:
            self.bind(user_input=submit_call)
        if validate_call is not None:
            self.ids["user_input"].bind(on_text_validate=validate_call)

    def get_user_input(self, *args):
        self.user_input = self.ids["user_input"].text


class SelectFromList(Popup):
    user_input = StringProperty()

    def __init__(self, heading=None, submit_call=None, list_heading=None, item_list=[], **kwargs):
        super(SelectFromList, self).__init__(**kwargs)
        self.title = heading if heading is not None else self.title
        self.ids["list_tree"].root_options = {"text": list_heading if list_heading is not None else self.title,
                                              "no_selection": True}
        for name in item_list:
            self.ids["list_tree"].add_node(TreeViewLabel(text=name))

        if submit_call is not None:
            self.bind(user_input=submit_call)

    def get_user_input(self, *args):
        self.user_input = self.ids["list_tree"].selected_node.text


class SelectSystemObject(Popup):
    selected_path = ObjectProperty()

    def __init__(self, heading=None, submit_call=None, path=None, dirselect=True, **kwargs):
        super(SelectSystemObject, self).__init__(**kwargs)
        self.title = heading if heading is not None else self.title
        self.ids["chooser"].path = path
        self.ids["chooser"].dirselect = dirselect

        if submit_call is not None:
            self.bind(selected_path=submit_call)


class Notification(Popup):

    def __init__(self, heading=None, info=None, **kwargs):
        super(Notification, self).__init__(**kwargs)
        self.title = heading if heading is not None else self.title
        self.ids["info"].text = info if info is not None else ""

