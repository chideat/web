# -*- coding: UTF-8 -*-

import smtplib

from ConfigParser import *


def send(_from, _to, subject, body, passwd):
    # port 465 or 587
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.login(_from, passwd)
    headers = '\r\n'.join(['from: ' + _from,
                           'subject: ' + subject,
                           'to: ' + _to,
                           'mime-version: 1.0',
                           'content-type: text/html'])
    content = headers + '\r\n\r\n' + body
    session.sendmail(_from, _to, content)


def mail(_to, subject, body):
    CF = ConfigParser()
    CF.read('mail.conf')
    conf = {}
    conf['from'] = CF.get('mail', 'from')
    conf['passwd'] = CF.get('mail', 'passwd')
    for item in _to:
        send(conf['from'], item, subject, body, conf['passwd'])
        print 'Sended mail to %s' % item



# mail(['chinaxiahaifeng@gmail.com'], 'web test', 'hello, this is a test mail')
