#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2014, 2016 Matt Nordhoff <mnordhoff@mattnordhoff.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# File format:
# https://dxr.mozilla.org/mozilla-central/rev/bfa85d23df57c8a1db17c99b267667becc1c4afd/toolkit/components/lz4/lz4.js#27,56-78
# (https://goo.gl/qKSLrx)
#
# In short, 'mozLz40\0' magic number + uint32le length + lz4 data.
#
# A comment in the file above claims that the magic number is 'mozLz4a\0', but
# this is incorrect, as demonstrated by the code next to the comment.
#
# Helpfully, Mozilla and python-lz4 chose the same length format, so I don't
# have to go out of my way to handle it.
#
# See also:
#
# http://bonardo.net/mozilla/2014/05/28/bookmarks-backups-respin.html
# https://bugzilla.mozilla.org/show_bug.cgi?id=818587

# Warning: Buffers everything in RAM.

import argparse
import sys

import lz4

_magic = 'mozLz40\0'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'name', default=[sys.stdin], nargs='*', type=argparse.FileType('rb'))
    args = parser.parse_args()
    for fh in args.name:
        magic = fh.read(len(_magic))
        if _magic != magic:
            raise ValueError("%s is not valid mozlz4: %r" % (fh.name, magic))
        sys.stdout.write(lz4.loads(fh.read()))

if __name__ == '__main__':
    main()
