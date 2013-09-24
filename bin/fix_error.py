#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import MySQLdb

conn = MySQLdb.connect(host='localhost', user='root', passwd='root', db='test', charset='utf8')

category = 'w'
with open('md5s.list', 'r') as f:
    cursor = conn.cursor()
    for line in f.readlines():
        print line
        line = line.strip()
        sql = 'update thumb set path="/{0}/{1}.jpg", category="{0}" where path like "%{1}%"'.format(category, line)
        print sql
        cursor.execute(sql)
    conn.commit()
    cursor.close()
conn.close()
