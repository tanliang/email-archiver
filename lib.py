#!/usr/bin/evn python
# -*- coding: utf-8 -*-
# author: leotan<tanjnr@gmail.com>

import poplib, email, sys, time
import hashlib, traceback
import string


class TBase:

    DEBUG = True
    
    def __init__(self):
        self.params = {}

    def setVal(self, key, val):
        self.params[key] = val

    def setPms(self, pms):
        self.params = pms

    def _log(self, _log):
        if self.__class__.DEBUG:

            now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            _log = now + " Log info: (" + \
                str(self.__class__) + \
                ") " + _log + "\n"

            print(_log)
            f = open(os.getcwd()+"tmp/log.txt", "a+")
            f.write(_log)
            f.close()


class TMail(TBase):

    def __init__ (self):
        TBase.__init__(self)
        self.CONN_FAIL = False
        self.CONN_SUCC = True
        self.M = None
        self.m_body = ""

    def __del__ (self):
        if self.M:
            self.M.quit()

    def _connect(self):
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

        for i in range(msg_num):
            mail = email.message_from_string(string.join(self.M.retr(i+1)[1], "\n"))
            m_title = self.getTitle(mail)
            self.m_body = ""
            self.fetchBody(mail)

            key = hashlib.md5(str(m_title))
            key = key.hexdigest()
            f = open("tmp/"+key+".msg", "w")
            f.write(self.m_body)
            f.close()

    def getTitle(self, mail):
        subject, t = email.Header.decode_header(mail["Subject"])[0]
        if t:
            subject = unicode(subject, t).encode("utf-8", "ignore")
        return subject

    def fetchBody(self, mail):
        if mail.is_multipart():
            for part in mail.get_payload():
                self.fetchBody(part)
        else:
            char = mail.get_content_charset()
            if char == None:
                self.m_body += mail.get_payload()
            else:
                try:
                    self.m_body += unicode(mail.get_payload(decode = True), char).encode('utf-8')
                except UnicodeDecodeError:
                    self.m_body += mail
                    _log = traceback.format_exc()
                    self._log(_log)


if __name__ == "__main__":

    M = TMail()
    M.setVal("host", "pop.qq.com")
    M.setVal("addr", "223272067@qq.com")
    M.setVal("pswd", "138880")
    M.getMsg()