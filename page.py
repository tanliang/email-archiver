#!/usr/bin/env python

"""Page

author: tanliang<tanjnr@gmail.com>

"""

from lib import *
import os, hashlib, base64
import urlparse
from stat import *

def getDirFileNum(m_name):
    return sum([int(os.path.isfile(os.path.join(m_name,files))) for files in os.listdir(m_name)])

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

        for i in os.listdir(c):
            m_name = os.path.join(c,i)
            if os.path.isfile(m_name):
                continue
            _t = os.stat(m_name)[ST_MTIME]
            _t = time.strftime(TBase.TFORMAT, time.localtime(float(_t)))
            _n = str(getDirFileNum(m_name))
            key = _t+"_"+i+"_"+_n

            f = open(m_name+".name")
            b = f.read()
            f.close()

            li_dict[key] = b

        for i in sorted(li_dict.keys(), key=lambda d:d.split("_")[0], reverse=True):
            m_name = li_dict[i]
            _t, _k, _n = i.split("_")
            res += "<li>["+_n+"]"+_t+" <a href=\"/more?c="+self.q["c"][0]+"&m="+base64.urlsafe_b64encode(m_name)+"\" target=\"_blank\">"+m_name+"</a></li>"

        res += "</ul>"
        return {"title":_c,"body":res}

    def get_more(self):
        res = "<ul>"
        c = self.d+os.sep+base64.urlsafe_b64decode(self.q["c"][0])
        _m = base64.urlsafe_b64decode(self.q["m"][0])
        key = hashlib.md5(str(_m))
        key = key.hexdigest()
        c += os.sep+key
        
        m_list = os.listdir(c)
        _count = 0
        for i in sorted(m_list, key=lambda d:d.split("_")[0]):
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
                    att_name = base64.urlsafe_b64decode(j)
                    att_suffix = att_name.split(".")[-1]
                    if att_suffix.lower() in ["jpg", "jpeg", "png", "bmp", "gif"]:
                        att += "<p>"+att_name+"<img src=\"/att?c="+self.q["c"][0]+"&m="+key+"&d="+i.rstrip(".msg")+"&a="+j+"\" alt=\""+att_name+"\"/></p>"
                    else:
                        att += "<p><a href=\"/att?c="+self.q["c"][0]+"&m="+key+"&d="+i.rstrip(".msg")+"&a="+j+"\">"+att_name+"</a></p>"
            
            res += "<li class=\"mail_body\"><h1><a name=\"next"+str(_count)+"\">"

            _count += 1
            res += "#"+str(_count)+" "+_m+"</a></h1>"
            tip_next = "Next"
            if _count == getDirFileNum(c):
                _count = 0
                tip_next = "Top"
            res += " <a href=\"#next"+str(_count)+"\">"+tip_next+"</a>"+att
            res += "<pre>"+b+"</pre><a href=\"#next0\">Top</a></li>"

        res += "</ul>"
        return {"title":_m,"body":res}

    def get_att(self):
        c = self.d+os.sep+base64.urlsafe_b64decode(self.q["c"][0])
        a = base64.urlsafe_b64decode(self.q["a"][0])
        p = c+os.sep+self.q["m"][0]+os.sep+self.q["d"][0]+os.sep+self.q["a"][0]
        print(p)
        return {"title":a,"body":p}
