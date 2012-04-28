#!/usr/bin/env python

"""Page

author: tanliang<tanjnr@gmail.com>

"""

from lib import *
import os, hashlib, base64
import urlparse
from stat import *

class Page(TBase):

    def __init__(self, query):
        self.c = Config()
        self.q = urlparse.parse_qs(query)
        self.d = os.getcwd()+os.sep+"data"

    def get_index(self):
        res = "<ul>"
        for i in self.c.getVal("emails"):
            catalog, email_info = i
            host, addr, pswd = email_info.split(":")
            res += "<li><a href=\"/list?c="+base64.urlsafe_b64encode(addr)+"\">"+catalog+"</a></li>"

        res += "</ul>"
        return {"title":"index","body":res}
    
    def get_list(self):
        res = "<ul>"
        _c = base64.urlsafe_b64decode(self.q["c"][0])
        c = self.d+os.sep+_c
        li_dict = {}
        li_sort = []

        for i in os.listdir(c):
            m_name = os.path.join(c,i)
            t = os.stat(m_name)[ST_MTIME]
            key = hashlib.md5(i)
            key = str(t)+"_"+key.hexdigest()
            li_dict[key] = i
            li_sort.append(key)

        li_sort.sort()
        for i in li_sort:
            m_name = li_dict[i]
            res += "<li><a href=\"/more?c="+self.q["c"][0]+"&m="+m_name+"\">"+base64.urlsafe_b64decode(m_name)+"</a></li>"

        res += "</ul>"
        return {"title":_c,"body":res}

    def get_more(self):
        res = "<ul>"
        c = self.d+os.sep+base64.urlsafe_b64decode(self.q["c"][0])
        _m = base64.urlsafe_b64decode(self.q["m"][0])
        c += os.sep+self.q["m"][0]
        
        m_list = os.listdir(c)
        m_list.sort()
        for i in m_list:
            f_name = os.path.join(c,i)
            if os.path.isdir(f_name):
                continue
            f = open(f_name)
            b = f.read()
            f.close()
            d_att = f_name.rstrip(".msg")
            att = ""
            if os.path.exists(d_att):
                for j in os.listdir(d_att):
                    #f_att = os.path.join(d_att,j)
                    att += "<a href=\"/att?c="+self.q["c"][0]+"&m="+self.q["m"][0]+"&d="+i.rstrip(".msg")+"&a="+j+"\">"+base64.urlsafe_b64decode(j)+"</a><br />"

            res += "<li style=\"margin-top:20px;border-top: 1px dashed #d00000;\"><h1>Mail Content:</h1><pre>"+b+"</pre>"+att+"</li>"

        res += "</ul>"
        return {"title":_m,"body":res}

    def get_att(self):
        c = self.d+os.sep+base64.urlsafe_b64decode(self.q["c"][0])
        a = base64.urlsafe_b64decode(self.q["a"][0])
        p = c+os.sep+self.q["m"][0]+os.sep+self.q["d"][0]+os.sep+self.q["a"][0]
        print(p)
        return {"title":a,"body":p}