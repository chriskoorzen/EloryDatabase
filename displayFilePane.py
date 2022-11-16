from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.stacklayout import StackLayout


class FileDisplayPane(RelativeLayout):

    def __init__(self, **kwargs):
        super(FileDisplayPane, self).__init__(**kwargs)
        self.add_widget(Label(text="File Display", size_hint=(1, 0.08), pos_hint={"top": 1}))
        bounding_box = BoxLayout(padding=[0,0,0,0], size_hint=(1, 0.6), pos_hint={"top": 0.92})
        self.file_display = Image(source="")
        with self.file_display.canvas:
            Color(0.3, 0.3, 0.3, 0.5)
            self.file_display.rect = Rectangle(size=self.file_display.size, pos=self.file_display.pos)
        self.file_display.bind(pos=self.update_img_background)
        self.file_display.bind(size=self.update_img_background)

        bounding_box.add_widget(self.file_display)
        self.add_widget(bounding_box)

        self.tag_display = StackLayout(size_hint=(1, 0.30), pos_hint={"top": 0.32}, padding=5)
        self.add_widget(self.tag_display)

    def set_active_image(self, *args):
        # Expect 2nd parameter to be filepath string
        print(*args)
        self.file_display.source = args[1]

    def update_img_background(self, *args):
        self.file_display.rect.pos = self.file_display.pos
        self.file_display.rect.size = self.file_display.size
