#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

from multiprocessing import Pool, Queue
import os
import time

define("port", default=8888, help="run on the given port", type=int)

def somefunc():
    time.sleep(0.2)
    return os.getpid()

class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        p = self.application.settings.get('pool')
        p.apply_async(somefunc,callback=self.async_callback(self.on_getpid))


    def on_getpid(self,pid):
        self.write(str(pid))
        self.finish()


def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", MainHandler),
    ], pool=Pool(4), queue=Queue())
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()