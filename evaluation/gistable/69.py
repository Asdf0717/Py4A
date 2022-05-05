###########################
# windows only
###########################

#import sublime
import sublime_plugin
import os
import os.path


class OpenInDefaultCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        os.system(self.view.file_name())


class CmdWindowHereCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        path = self.view.file_name()
        dirPath = os.path.dirname(path)
        cmd = 'start /D"%(dirPath)s"' % {'dirPath': dirPath}
        #print cmd
        os.system(cmd)


cygBinPath = 'c:\\cygwin\\bin'


def to_cygpath(path):
    return os.popen('%(cygBinPath)s\\cygpath "%(path)s"' % {'cygBinPath': cygBinPath, 'path': path}).read().rstrip()


class BashPromptHereCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        path = self.view.file_name()
        dirPath = os.path.dirname(path)
        cP = to_cygpath(dirPath)
        cmd = 'start %(cygBinPath)s\\bash --login -i -c "cd \\"%(cP)s\\"; exec bash"' % {'cygBinPath': cygBinPath, 'cP': cP}
        #print cmd
        os.system(cmd)
