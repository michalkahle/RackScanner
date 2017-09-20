import sys
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import importlib
import StringIO
import urllib

class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        """Version of send_head that support runing python modules."""
        if self.client_address[0] <> '127.0.0.1':
            self.send_error(501, 'Only local host allowed')
            return False
        path, _, query = self.path.partition('?')
        if self.is_cgi(path):
            return self.run_cgi(path, query)
        else:
            return SimpleHTTPRequestHandler.send_head(self)

    def is_cgi(self, path):
        return True if path in ('/', '/platescan', '/test') else False
    
    def run_cgi(self, path, query):
        dic = self.parse_query(query)
        module, fn = ('platescan', 'main')
        try:
            m = importlib.import_module(module)
#            m = __import__(module, globals(), locals(), [fn])
            # if dic.get('reload'):
            reload(m)
        except:
            self.send_error(404, 'Failed to import %s (%s, %s)' % ((module,) + sys.exc_info()[:2]))
            return None
        try:
            func = getattr(m, fn)
        except:
            self.send_error(404, 'Module %s has no function %s (%s %s)' % ((module, fn) + sys.exc_info()[:2]))
            return None
        oo = sys.stdout
        try:
            io = StringIO.StringIO()
            sys.stdout = io
            res = func(**dic)
            defaults = {'Content-Type':'text/html'}
            if isinstance(res, dict):
                defaults.update(res)
            self.send_response(200)
            self.send_header("Content-type", defaults['Content-Type'])
            self.send_header("Content-Length", str(io.len))
            self.end_headers()
            io.seek(0)
            self.copyfile(io, self.wfile)
        finally:
            sys.stdout = oo
        return None
    
    def parse_query(self, query):
        dic = {}
        query = urllib.unquote(query)
        for par in query.replace('+',' ').split('&'):
            kv = par.split('=', 1)
            if len(kv) == 2:
                name, value = kv
                if dic.has_key(name):
                    oldvalue = dic[name]
                    if isinstance(oldvalue, basestring):
                        dic[name] = [oldvalue, value]
                    else:
                        dic[name].append(value)
                else:
                    dic[name] = value
        return dic

if __name__ == '__main__':
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 8000
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, Handler)
    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()
