import traceback


class WebApp(object):
    def __init__(self, obj):
        self.obj = obj

    def __call__(self, environ, start_response):
        try:
            path = filter(bool, environ["PATH_INFO"].split("/"))
            try:
                method = path.pop(0)
            except IndexError:
                res = self.obj
            else:
                res = getattr(self.obj, method)(*path)
            start_response("200 OK", {})
            return [str(res)]
        except Exception:
            start_response("500 INTERNAL SERVER ERROR", {})
            return [traceback.format_exc()]


application = WebApp([])