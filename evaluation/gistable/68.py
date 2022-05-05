#!/usr/bin/python

from Foundation import NSWorkspace, NSURL
import urllib

def show_gists():
    NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_('https://gist.github.com/search?q=%40pudquick&ref=searchresults'))

def search_gists(search_string):
    NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_('https://gist.github.com/search?q=%%40pudquick+%s&ref=searchresults' % search_string))
