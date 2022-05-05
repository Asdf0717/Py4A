import sublime_plugin
import sublime
import time
import os


class MyEvents(sublime_plugin.EventListener):
    def on_deactivated_async(self, view):
        s = view.file_name()
        if s:
            time.sleep(0.1)  # Give the file time to be removed from the filesystem
            if not os.path.exists(s):
                print("Closing view", s)
                view.set_scratch(True)
                view.window().run_command("close_file")