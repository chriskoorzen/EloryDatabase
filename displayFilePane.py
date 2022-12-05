from sqlite3 import IntegrityError

from kivy.properties import ObjectProperty, DictProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout

from databaseObjects import File


class FileDisplayPane(RelativeLayout):
    active_file = ObjectProperty()
    active_tags = DictProperty()

    db = ObjectProperty()
    files = ObjectProperty()
    groups = ObjectProperty()
    tags = ObjectProperty()

    def __init__(self, **kwargs):
        super(FileDisplayPane, self).__init__(**kwargs)
        # print("FilePane init")
        # print("FilePane db:", hex(id(self.db)))
        # print("FilePane files:", hex(id(self.files)))
        # print("FilePane groups:", hex(id(self.groups)))
        # print("FilePane tags:", hex(id(self.tags)))

    def on_kv_post(self, base_widget):
        # print("FilePane on_kv_post")
        # print("FilePane db:", hex(id(self.db)))
        # print("FilePane files:", hex(id(self.files)))
        # print("FilePane groups:", hex(id(self.groups)))
        # print("FilePane tags:", hex(id(self.tags)))
        pass

    def on_active_file(self, *args):
        # Display the selected file - gets update from File Manager
        self.ids["file_display"].source = self.active_file
        if not self.ids["file_display"]._coreimage:     # No convenient exposed property to see if image failed to load
            print("This failed to load - Set a default image for failure")

        # Load tags of selected file
        self.ids["tag_display"].clear_widgets()         # Clear the display widget
        self.active_tags.clear()                        # Clear the list of modified tags
        if self.active_file in self.files:              # Does this file exist in the db?
            for tag in self.files[self.active_file].tags.values():
                display_tag = TagButton(0, tag, on_press=self.toggle_tag_status)
                self.active_tags[tag.db_id] = display_tag      # Loaded tags status = 0 (no change)
                self.ids["tag_display"].add_widget(display_tag)

    def toggle_tag_status(self, tag_button):
        """
        -1 - Delete         (Remove this tag from file)
         0 - No change      (Don't modify this tag)
         1 - Add            (Add this tag to file)
        """
        if tag_button.status == 0:
            # if default, delete (-1)
            tag_button.status = -1
            tag_button.color = [1, 0, 0, 1]     # Red
        elif tag_button.status == -1:
            # if delete, revert back to default
            tag_button.status = 0
            tag_button.color = [1, 1, 1, 1]     # White
        elif tag_button.status == 1:
            # if add, don't modify, remove from list
            del self.active_tags[tag_button.tag.db_id]          # remove from active tags
            self.ids["tag_display"].remove_widget(tag_button)   # remove from display

    def add_new_tag(self, *args):
        tag_obj = args[0].db_object
        if not self.active_file:        # don't do anything if active file is not set
            return
        if tag_obj.db_id not in self.active_tags:
            display_tag = TagButton(1, tag_obj, on_press=self.toggle_tag_status, color=[0, 1, 0, 1])    # Green
            self.active_tags[tag_obj.db_id] = display_tag  # Loaded tags status = 1 (Add to file)
            self.ids["tag_display"].add_widget(display_tag)

    def save_changes(self):

        # Add the file if not in db
        if self.active_file not in self.files:
            new_file = File.new_file(self.active_file, self.db)
            if not new_file:
                print("Error")
                return
            mod_file = new_file
            # Update Model
            self.files[new_file.path] = new_file
            # Update View ?
        else:
            mod_file = self.files[self.active_file]

        add_list = []
        del_list = []
        # Read the mod parameters of the tags in the display pane
        for tag_btn in self.active_tags.values():       # Values expected: [status: int, tag_btn: TagButton]
            # print("Tag status:", status, " -- tag:", tag_btn)
            if not tag_btn.status:
                continue    # Don't modify tags with status 0
            elif tag_btn.status == 1:
                # Add new
                add_list.append(tag_btn)
            elif tag_btn.status == -1:
                del_list.append(tag_btn)

        # Add tags
        mod_file.add_tags(self.db, *[x.tag for x in add_list])
        # Update tag display
        for i in add_list:
            i.color = [1, 1, 1, 1]      # Update View, White
            i.status = 0                # Update Model

        # Delete tags
        mod_file.remove_tags(self.db, *[x.tag for x in del_list])
        # Update tag display
        for i in del_list:
            self.ids["tag_display"].remove_widget(i)    # Update View
            del self.active_tags[i.tag.db_id]           # Update Model


class TagButton(Button):
    status = NumericProperty()

    def __init__(self, status, tag_obj, **kwargs):
        super(TagButton, self).__init__(**kwargs)
        self.status = status
        self.text = tag_obj.name
        self.tag = tag_obj
