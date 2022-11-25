from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout


class FileDisplayPane(RelativeLayout):

    def __init__(self, **kwargs):
        super(FileDisplayPane, self).__init__(**kwargs)

    def set_active_object(self, *args):
        # 2nd parameter is object with 'path' member
        file_object = args[1]
        self.ids["file_display"].source = file_object.path     # Set Image path

        # Getting tags for file object
        self.ids["tag_display"].clear_widgets()    # Clean tags on each update
        if type(file_object) != type:       # Filter out 'Anon' objects -> Part of workaround
            for tag in file_object.tags.values():
                # TODO define custom widget for Tag displays -> click func to remove or edit from current tagged file
                display_tag = Button(text=f"{tag.name}", size_hint=(None, None), padding=(12, 12))
                display_tag.bind(texture_size=display_tag.setter("size"))    # Bind widget size directly to texture size
                self.ids["tag_display"].add_widget(display_tag)

    def get_selected_tag(self, *args):
        print("Got tag ->", *args)
        tag = args[1].db_object
        # TODO define custom widget for Tag displays -> click func to remove or edit from current tagged file
        display_tag = Button(text=f"{tag.name}", size_hint=(None, None), padding=(12, 12))
        display_tag.bind(texture_size=display_tag.setter("size"))  # Bind widget size directly to texture size
        # TODO need to be able to uniquely identify displayTags, so that we don't add it multiple times
        self.ids["tag_display"].add_widget(display_tag)
