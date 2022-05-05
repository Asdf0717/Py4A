'''
Example of Tornado that autoreloads/watches all files in folder 'static'
'''
import tornado.ioloop
import tornado.web
import tornado.autoreload
import os


''' serves index.html'''
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/index.html')


application = tornado.web.Application([
    (r'/', MainHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static/'})
],gzip=True)


if __name__ == "__main__":
    application.listen(8888)

    #TODO remove in prod
    tornado.autoreload.start()
    for dir, _, files in os.walk('static'):
        [tornado.autoreload.watch(dir + '/' + f) for f in files if not f.startswith('.')]

    tornado.ioloop.IOLoop.instance().start()
