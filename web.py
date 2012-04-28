#!/usr/bin/env python

"""Simple HTTP Server.

author: tanliang<tanjnr@gmail.com>

"""

from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse, os, traceback
from page import Page

class GetHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        """
        message = '\n'.join([
          'CLIENT VALUES:',
          'client_address=%s (%s)' % (self.client_address, self.address_string()),
          'command=%s' % self.command,
          'path=%s' % self.path,
          'real path=%s' % parsed_path.path,
          'query=%s' % parsed_path.query,
          'request_version=%s' % self.request_version,
          '',
          'SERVER VALUES:',
          'server_version=%s' % self.server_version,
          'sys_version=%s' % self.sys_version,
          'protocol_version=%s' % self.protocol_version,
          '',
        ])
        """
        self.send_response(200)

        #self.wfile.write(message)
        _p = str(parsed_path.path)
        if _p == "/":
            _p = "/index"
        
        try:
            page = getattr(Page(parsed_path.query), "get_"+_p[1:])()
        except:
            _log = traceback.format_exc()
            print(_log)
            page = {"title":"nothing","body":"nothing here"}

        if _p == "/att":
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Disposition", "attachment;filename=\""+page["title"]+"\"")

            tpl = ""
            if os.path.exists(page["body"]):
                f = open(page["body"], "rb")
                tpl = f.read()
                f.close()
        else:
            self.send_header("Content-type", "text/html")

            f = open(os.getcwd()+os.sep+"tpl.txt")
            tpl = f.read()
            f.close()

            for k,v in page.iteritems():
                tpl = tpl.replace("$"+k, v)

        self.end_headers()
        self.wfile.write(tpl)
        return

if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('localhost', 8080), GetHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()