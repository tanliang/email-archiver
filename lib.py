#!/usr/bin/evn python
# -*- coding: utf-8 -*-

"""Fetch Email to local directory.

This module builds on poplib, email etc by fetching email data to local
directory for later reference display.

author: tanliang<tanjnr@gmail.com>

"""

import poplib, email, sys, time
import hashlib, traceback
import string, os, datetime
from ConfigParser import ConfigParser
import threading, base64

class TBase:

    TFORMAT = "%Y-%m-%d %H:%M:%S"
    DEBUG = False
    
    def __init__(self):
        self.params = {}

    def setVal(self, key, val):
        self.params[key] = val

    def setPms(self, pms):
        self.params = pms

    def _log(self, _log):
        tf = self.__class__.TFORMAT
        now = time.strftime(tf, time.localtime())
        _log = now + " Log info: (" + \
            str(self.__class__) + \
            ") " + _log + "\n"

        if self.__class__.DEBUG:
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
            try:
                os.mkdir(t_dir)
            except:
                pass
        return t_dir

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
        f_name, t = email.Header.decode_header(self.mail.get_filename())[0]
        if t:
            f_name = f_name.decode(t, "ignore").encode("utf-8")

        f_more = self.mail.get_payload(decode = True)
        self._m.fwrite(self.m_dir, base64.urlsafe_b64encode(f_name), f_more, "wb")

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
        data_dir = "data"+os.sep
        p_dir = data_dir+self.params["addr"]

        for i in range(msg_num):
            idx = i+1
            mail = email.message_from_string(string.join(self.M.retr(idx)[1], "\n"))
            m_title = str(self.getTitle(mail))
            b64_title = base64.urlsafe_b64encode(m_title)
            m_date = self.getDate(mail)

            key = hashlib.md5(str(m_title))
            key = key.hexdigest()
            self.m_body = ""
            self.m_more = {}
            try:
                m_dir = p_dir+os.sep+key
                if os.path.exists(m_dir+".name") == False:
                    self.fwrite(p_dir, key+".name", m_title)

                f_name = m_date+"_"+key
                self.fetchBody(mail, m_dir+os.sep+f_name)
                self.fwrite(m_dir, f_name+".msg", self.m_body)
            except:
                _log = traceback.format_exc()
                self._log(_log)
                unparsed = data_dir+"unparsed"
                self.fwrite(unparsed, m_date+"_"+b64_title+".msg", mail)
            
            if TBase.DEBUG == False:
                self.M.dele(idx)

    def getTitle(self, mail):
        subject, t = email.Header.decode_header(mail["Subject"])[0]
        if t:
            subject = subject.decode(t, "ignore").encode("utf-8")
        res = subject.split(":")[-1].strip()
        if res == "":
            res = subject
            self._log("subject parse error")
            self._log(res)
        return res

    def getDate(self, mail):
        _data = " ".join(mail['Date'].split(" ")[1:5])
        _date = time.strptime(_data, "%d %b %Y %H:%M:%S")
        return time.strftime("%Y%m%d%H%M%S", _date)

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
            self.m_body += mail.get_payload(decode = True).decode(char, "ignore").encode('utf-8')

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
        if key:
            return self.c.get(section, key)
        return self.c.items(section)



if __name__ == "__main__":

    c = Config()

    try:
        _debug = c.getVal("system", "debug")
        if _debug == "true":
            TBase.DEBUG = True
    except:
        pass
    
    for i in c.getVal("emails"):
        catalog, email_info = i
        host, addr, pswd = email_info.split(":")

        t = TMailThread()
        t.init(host, addr, pswd)
        t.start()
