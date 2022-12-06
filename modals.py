from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.treeview import TreeViewLabel
from kivy.factory import Factory

import logging
modal_logger = logging.getLogger(__name__)
modal_logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(fmt)
modal_logger.addHandler(handler)
modal_logger.propagate = False


class Notification(Popup):

    def __init__(self, heading=None, info=None, **kwargs):
        super(Notification, self).__init__(**kwargs)
        self.title = heading if heading is not None else self.title
        self.ids["info"].text = info if info is not None else ""

    def on_open(self):
        modal_logger.info(f"Launched Popup window '{self.__class__}' {self.title}")
        super(Notification, self).on_open()


class UserInputBase(Popup):      # Base class for UserInput Modals
    user_input = ListProperty()

    def __init__(self, heading=None, submit_call=None, **kwargs):
        # Replace "Placeholder" Widget with intended template
        Factory.unregister("Placeholder")
        Factory.register("Placeholder", cls=self.placeholder)
        super(UserInputBase, self).__init__(**kwargs)

        self.title = heading if heading is not None else self.title

        if submit_call is not None:
            self.bind(user_input=submit_call)

    def get_user_input(self, *args):
        pass
    
    def on_open(self):
        modal_logger.info(f"Launched Popup window '{self.__class__}' {self.title}")
        super(UserInputBase, self).on_open()


class TextAndInfo(BoxLayout):
    pass


class TextInfoAndOption(TextAndInfo):
    pass


class UserInputBox(UserInputBase):
    placeholder = TextAndInfo

    def __init__(self, info=None, text_descript=None, **kwargs):
        super(UserInputBox, self).__init__(**kwargs)
        self.ids["placeholder"].ids["info"].text = info if info is not None else ""
        self.ids["placeholder"].ids["user_input"].hint_text = text_descript if text_descript is not None else ""

    def get_user_input(self, *args):
        if self.ids["placeholder"].ids["user_input"].text == "":    # Don't process empty strings
            return True
        self.user_input = [self.ids["placeholder"].ids["user_input"].text]
        self.dismiss()


class UserInputWithOption(UserInputBox):
    placeholder = TextInfoAndOption

    def __init__(self, info=None, text_descript=None, **kwargs):
        super(UserInputWithOption, self).__init__(**kwargs)
        self.ids["placeholder"].ids["info"].text = info if info is not None else ""
        self.ids["placeholder"].ids["user_input"].hint_text = text_descript if text_descript is not None else ""

    def get_user_input(self, *args):
        if self.ids["placeholder"].ids["user_input"].text == "":    # Don't process empty strings
            return True
        self.user_input = [self.ids["placeholder"].ids["user_input"].text,
                           self.ids["placeholder"].ids["check_option"].state]
        self.dismiss()


class OptionList(ScrollView):
    pass


class SelectFromList(UserInputBase):
    placeholder = OptionList

    def __init__(self, list_heading=None, item_list=[], **kwargs):
        super(SelectFromList, self).__init__(size=(400, 350), **kwargs)
        self.ids["placeholder"].ids["list_tree"].root_options = \
            {"text": list_heading if list_heading is not None else self.title, "no_selection": True}
        for name in item_list:
            self.ids["placeholder"].ids["list_tree"].add_node(TreeViewLabel(text=name))

    def get_user_input(self, *args):
        if self.ids["placeholder"].ids["list_tree"].selected_node is None:
            return True
        self.user_input = [self.ids["placeholder"].ids["list_tree"].selected_node.text]
        self.dismiss()


class SelectSystemObject(UserInputBase):
    placeholder = FileChooserIconView

    def __init__(self, path=None, dirselect=True, **kwargs):
        super(SelectSystemObject, self).__init__(size_hint=(0.5, 0.7), **kwargs)
        self.ids["placeholder"].size_hint = (1, 0.8)
        self.ids["placeholder"].pos_hint = {"top": 0.9}
        self.ids["placeholder"].path = path
        self.ids["placeholder"].dirselect = dirselect

    def get_user_input(self, *args):
        if self.ids["placeholder"].selection == []:
            return True
        self.user_input = [self.ids["placeholder"].selection]
        self.dismiss()
