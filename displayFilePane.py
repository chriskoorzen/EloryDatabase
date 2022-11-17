from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget


class FileDisplayPane(RelativeLayout):

    def __init__(self, **kwargs):
        super(FileDisplayPane, self).__init__(**kwargs)
        self.add_widget(Label(text="File Display", size_hint=(1, 0.08), pos_hint={"top": 1}))
        bounding_box = BoxLayout(padding=[0, 0, 0, 0], size_hint=(1, 0.6), pos_hint={"top": 0.92})
        self.file_display = Image(source="")
        with self.file_display.canvas:
            Color(0.3, 0.3, 0.3, 0.5)
            self.file_display.rect = Rectangle(size=self.file_display.size, pos=self.file_display.pos)
        self.file_display.bind(pos=self.update_img_background)
        self.file_display.bind(size=self.update_img_background)

        bounding_box.add_widget(self.file_display)
        self.add_widget(bounding_box)

        self.tag_display = StackLayout(size_hint=(1, 0.30), pos_hint={"top": 0.32}, padding=12, orientation='lr-tb', spacing=5)
        self.add_widget(self.tag_display)

    def set_active_object(self, *args):
        # 2nd parameter is object with 'path' member
        file_object = args[1]
        self.file_display.source = file_object.path     # Set Image path

        # Getting tags for file object
        self.tag_display.clear_widgets()    # Clean tags on each update
        if type(file_object) != type:       # Identify 'Anon' objects and exclude
            for tag in file_object.tags.values():
                # TODO define custom widget for Tag displays -> click func to remove or edit from current tagged file
                display_tag = Button(text=f"{tag.group.name}: {tag.name}", size_hint=(None, None), padding=(12, 12))
                display_tag.bind(texture_size=display_tag.setter("size"))    # Bind widget size directly to texture size
                self.tag_display.add_widget(display_tag)

    def get_selected_tag(self, *args):
        print("Got tag ->", *args)
        tag = args[1].db_object
        # TODO define custom widget for Tag displays -> click func to remove or edit from current tagged file
        display_tag = Button(text=f"{tag.group.name}: {tag.name}", size_hint=(None, None), padding=(12, 12))
        display_tag.bind(texture_size=display_tag.setter("size"))  # Bind widget size directly to texture size
        # TODO need to be able to uniquely identify displayTags, so that we don't add it multiple times
        self.tag_display.add_widget(display_tag)

    def update_img_background(self, *args):
        self.file_display.rect.pos = self.file_display.pos
        self.file_display.rect.size = self.file_display.size
