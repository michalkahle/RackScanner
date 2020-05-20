import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import importlib
import io
import urllib.request, urllib.parse, urllib.error
import traceback
import web_app

class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.client_address[0] != '127.0.0.1':
            self.send_error(501, 'Only local host allowed')
            return False
        path, _, query = self.path.partition('?')
        if path == '/':
            self.do_CGI(query)
        else:
            return super().do_GET()

    def do_CGI(self, query):
        dic = self.parse_query(query)
        sdout = sys.stdout
        importlib.reload(web_app)
        stringio = io.StringIO()
        sys.stdout = stringio
        try:
            web_app.run(**dic)
        except:
            print('<pre>%s</pre>' % traceback.format_exc())
        finally:
            self.send_response(200)
            self.send_header("Content-type", 'text/html')
            self.end_headers()
            self.wfile.write(stringio.getvalue().encode('utf-8'))
            sys.stdout = sdout
            stringio.close()

    def parse_query(self, query):
        dic = {}
        query = urllib.parse.unquote(query)
        for par in query.replace('+',' ').split('&'):
            kv = par.split('=', 1)
            if len(kv) == 2:
                name, value = kv
                if name in dic:
                    oldvalue = dic[name]
                    if isinstance(oldvalue, str):
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
    httpd = HTTPServer(server_address, RequestHandler)
    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    httpd.serve_forever()
