#!/usr/bin/evn python
# -*- coding: utf-8 -*-
# author: leotan<tanjnr@gmail.com>

import poplib, email, sys, time
import hashlib, traceback
import string, os, datetime
from ConfigParser import ConfigParser
import threading, base64

class TBase:

    TFORMAT = "%Y-%m-%d %H:%M:%S"
    DEBUG = True
    
    def __init__(self):
        self.params = {}

    def setVal(self, key, val):
        self.params[key] = val

    def setPms(self, pms):
        self.params = pms

    def _log(self, _log):
        if self.__class__.DEBUG == False:
            return
        
        tf = self.__class__.TFORMAT
        now = time.strftime(tf, time.localtime())
        _log = now + " Log info: (" + \
            str(self.__class__) + \
            ") " + _log + "\n"

        print(_log)
        self.fwrite("", "log.txt", _log, "a+")

    def fwrite(self, p_dir, p_file, f_body, f_mode="w"):
        t_dir = self.multiDir(os.getcwd(), p_dir)
        f = open(t_dir+os.sep+p_file, f_mode)
        f.write(str(f_body))
        f.close()

    def multiDir(self, b_dir, p_dir):
        t_dir = b_dir+os.sep+p_dir
        if os.path.exists(t_dir) or p_dir.find(os.sep) == -1:
            return t_dir

        m_dir = ""
        for i in p_dir.split(os.sep):
            m_dir += os.sep+i
            t_dir = b_dir+m_dir
            if os.path.exists(t_dir):
                continue
            os.mkdir(t_dir)
        return t_dir

    def base64Encode(self, raw_str):
        safe_rep = {"+":"(","/":")"}
        res = base64.b64encode(str(raw_str))
        for k,v in safe_rep.iteritems():
            res = res.replace(k,v)
        return res

    def base64Decode(self, raw_str):
        back_rep = {"(":"+",")":"/"}
        for k,v in back_rep.iteritems():
            raw_str = raw_str.replace(k,v)
        return base64.b64decode(raw_str)

class TMailThread(threading.Thread):

    def init(self, host, addr, pswd):
        self.M = TMail()
        self.M.setVal("host", host)
        self.M.setVal("addr", addr)
        self.M.setVal("pswd", pswd)

    def run(self):
        self.M.getMsg()

class TMailMoreThread(threading.Thread):
    
    def init(self, _m, mail, m_dir):
        self.mail = mail
        self.m_dir = m_dir
        self._m = _m

    def run(self):
        f_name = self.mail.get_filename()
        f_more = self.mail.get_payload(decode = True)
        #self._m.m_more[f_name] = f_more
        self._m.fwrite(self.m_dir, f_name, f_more, "wb")

class TMail(TBase):

    def __init__ (self):
        TBase.__init__(self)
        self.CONN_FAIL = False
        self.CONN_SUCC = True
        self.M = None
        self.m_body = ""
        self.m_more = {}

    def __del__ (self):
        if self.M:
            self.M.quit()

    def _connect(self):

        if self.M:
            return self.M

        conn_res = self.CONN_FAIL
        retry = 0

        while conn_res == self.CONN_FAIL and retry < 9:
            try:
                _log = "Connect to %s with %s" % (self.params["host"], self.params["addr"])
                self._log(_log)
                self.M = poplib.POP3(self.params["host"])
                self.M.user(self.params["addr"])
                self.M.pass_(self.params["pswd"])
                conn_res = self.CONN_SUCC
            except:
                _log = traceback.format_exc()
                self._log(_log)
                retry = retry + 1
                time.sleep(retry*10)

        if conn_res == self.CONN_FAIL:
            _log = "Email address %s unavailable!" % self.params["addr"]
            self._log(_log)
            sys.exit(1) 

    def getMsg(self):
        self._connect()
        msg_num = len(self.M.list()[1])
        p_dir = "data"+os.sep+self.params["addr"]

        for i in range(msg_num):
            idx = i+1
            mail = email.message_from_string(string.join(self.M.retr(idx)[1], "\n"))
            m_title = str(self.getTitle(mail))
            b64_title = self.base64Encode(m_title)
            _data = " ".join(mail['Date'].split(" ")[1:5])
            _date = time.strptime(_data, "%d %b %Y %H:%M:%S")
            m_date = time.strftime("%Y%m%d-%H%M%S", _date)

            key = hashlib.md5(str(m_title))
            key = key.hexdigest()
            self.m_body = ""
            self.m_more = {}
            try:
                m_dir = p_dir+os.sep+b64_title
                f_name = m_date+"_"+key
                self.fetchBody(mail, m_dir+os.sep+f_name)
                self.fwrite(m_dir, f_name+".msg", self.m_body)
            except:
                unparsed = p_dir+os.sep+"unparsed"
                self.fwrite(unparsed, m_date+"_"+b64_title+".msg", mail)

            #self.M.dele(idx)

    def getTitle(self, mail):
        subject, t = email.Header.decode_header(mail["Subject"])[0]
        if t:
            subject = unicode(subject, t).encode("utf-8", "ignore")

        c = Config()
        strips = c.getVal("system", "strips")
        for i in strips.split("|"):
            subject = subject.lstrip(i)
        return subject.strip()

    def fetchBody(self, mail, m_dir):
        if mail.is_multipart():
            for part in mail.get_payload():
                self.fetchBody(part, m_dir)
        else:
            t = mail.get_content_type()[0:4]
            if t == "text":
                self._getBody(mail)
            else:
                mt = TMailMoreThread()
                mt.init(self, mail, m_dir)
                mt.start()
            
    def _getBody(self, mail):
        char = mail.get_content_charset()
        if char == None:
            self.m_body += mail.get_payload(decode = True)
        else:
            try:
                self.m_body += unicode(mail.get_payload(decode = True), char).encode('utf-8')
            except UnicodeDecodeError:
                exctype, err_msg = sys.exc_info()[:2]
                char, junk = str(err_msg).split(" ", 1)
                char = char.strip("'")
                if char:
                    self.m_body += mail.get_payload(decode = True).decode(char).encode('utf-8')
                    _log = self.params["addr"]+" "+char+"\n"
                    self._log(_log)
                else:
                    _log = traceback.format_exc()
                    self._log(_log)
                    raise UnicodeDecodeError, "invalid unicode!"

class Config(TBase):

    def __init__(self, ini_file=""):
        if ini_file == "":
            ini_file = os.getcwd()+os.sep+"config.ini"
        self.f = open(ini_file)
        self.c = ConfigParser()
        self.c.readfp(self.f)

    def __del__(self):
        if self.f:
            self.f.close()

    def getVal(self, section, key=""):
        try:
            return self._getVal(section, key)
        except:
            _log = traceback.format_exc()
            self._log(_log)
            sys.exit(1) 

    def _getVal(self, section, key=""):
        if key:
            return self.c.get(section, key)
        else:
            return self.c.items(section)



if __name__ == "__main__":

    c = Config()
    
    for i in c.getVal("emails"):
        catalog, email_info = i
        host, addr, pswd = email_info.split(":")

        t = TMailThread()
        t.init(host, addr, pswd)
        t.start()


