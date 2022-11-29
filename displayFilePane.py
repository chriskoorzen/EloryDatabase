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
        self.ids["file_display"].source = self.active_file.path
        if not self.ids["file_display"]._coreimage:     # No convenient exposed property to see if image failed to load
            print("This failed to load - Set a default image for failure")

        # Load tags of selected file
        self.ids["tag_display"].clear_widgets()
        self.active_tags.clear()
        for tag in self.active_file.tags:
            display_tag = TagButton(0, self.tags[tag], on_press=self.toggle_tag_status)
            self.active_tags[tag] = display_tag      # Loaded tags status = 0 (no change)
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
        mod_file = self.active_file
        if (type(mod_file) == type) and (len(self.active_tags) > 0):
            # This is an anon object, has not been added to db yet
            try:
                file_id, file_hash = self.db.create_entry("file", [{'file_path': mod_file.path}])[0]  # Expect a list with 1 tuple
            except IntegrityError as errmsg:
                print("Cannot add this file to database:", errmsg)
                return
            except TypeError as errmsg:
                print("Cant unpack tuple because:", errmsg)
                return
            # Update Model
            mod_file = File(file_id, mod_file.path, file_hash)
            self.files[file_id] = mod_file
            # Update View ?

        add_list = []
        del_list = []
        for tag_btn in self.active_tags.values():       # Values expected: [status: int, tag_btn: TagButton]
            # print("Tag status:", status, " -- tag:", tag_btn)
            if not tag_btn.status:
                continue    # Don't modify tags with status 0
            elif tag_btn.status == 1:
                # Add new
                add_list.append(tag_btn)
            elif tag_btn.status == -1:
                del_list.append(tag_btn)
        # TODO What if an insertion or deletion fails?
        try:
            self.db.create_entry("tag-file", [{'file_id': mod_file.db_id, 'tag_id': x.tag.db_id} for x in add_list])
        except IntegrityError as errmsg:
            print(errmsg)
            return
        # link tags to files
        for i in add_list:
            mod_file.tags.add(i.tag.db_id)
            i.tag.files.add(mod_file.db_id)
            i.color = [1, 1, 1, 1]      # Update View, White
            i.status = 0                # Update Model

        try:
            self.db.delete_entry("tag-file", [{'file_id': mod_file.db_id, 'tag_id': x.tag.db_id} for x in del_list])
        except IntegrityError as errmsg:
            print(errmsg)
            return
        # link tags to files
        for i in del_list:
            mod_file.tags.remove(i.tag.db_id)
            i.tag.files.remove(mod_file.db_id)
            self.ids["tag_display"].remove_widget(i)    # Update View
            del self.active_tags[i.tag.db_id]           # Update Model


class TagButton(Button):
    status = NumericProperty()

    def __init__(self, status, tag_obj, **kwargs):
        super(TagButton, self).__init__(**kwargs)
        self.status = status
        self.text = tag_obj.name
        self.tag = tag_obj
