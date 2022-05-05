import sublime
import sublime_plugin
import webbrowser


class OpenUrlCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = self.view.sel()[0]

        # Expand selection to possible URL
        start = s.a
        end = s.b

        view_size = self.view.size()
        terminator = ['\t', ' ', '\"', '\'', '(', ')']

        while (start > 0
                and not self.view.substr(start - 1) in terminator
                and self.view.classify(start) & sublime.CLASS_LINE_START == 0):
            start -= 1

        while (end < view_size
                and not self.view.substr(end) in terminator
                and self.view.classify(end) & sublime.CLASS_LINE_END == 0):
            end += 1

        # Check if this is URL
        url = self.view.substr(sublime.Region(start, end))
        print("URL : " + url)

        if url.startswith(('http://', 'https://')):
            webbrowser.open_new_tab(url)
        else:
            print("not URL")
