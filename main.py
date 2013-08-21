#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import time
import datetime
import json
import Image
import bottle
import bottle_mysql

from bottle import route, run, template, request, response
from mail import *

conn = bottle_mysql.Plugin(dbuser='root',
                         dbpass='root',
                         dbname='test',
                         dbhost='127.0.0.1')

app = bottle.Bottle()
app.install(conn)


def query(db, sql):
    db.connection.set_character_set('utf8')
    db.execute('SET NAMES UTF8;')
    db.execute('SET CHARACTER SET utf8;')
    db.execute('SET character_set_connection=utf8;')
    count = db.execute(sql)
    if count > 0:
        return db.fetchall()
    else:
       return None


def _crop(db, data):
    Home = os.path.expanduser('~') + '/Data'
    Root = '%s/%s' % (Home, 'Temp')
    Thumb = '%s/Thumb' % (Home)
    Log = '%s/%s' % (Home, 'Trash/log')
    source = '%s/%s' % (Home, data['src'])
    if not os.path.exists(Root):
        os.mkdir(Root)
    if not os.path.exists(Thumb):
        os.mkdir(Thumb)
    cate = ''
    if data['cate']:
        cate = data['cate']
    else:
        cate = data['src'].rsplit('/', 2)[-2]
    _cate = '%s/%s' % (Root, cate)
    _thumb = '%s/%s' % (Thumb, cate)
    if data['crop'] == '1':
        if not os.path.exists(_cate):
            os.mkdir(_cate)
        if not os.path.exists(_thumb):
            os.mkdir(_thumb)
        im = Image.open(source)
        pic_name = str(int(time.time() * 10 ** 6))
        save = '%s/%s.jpg' % (_cate, pic_name)
        save_thumb = '%s/%s.jpg' % (_thumb, pic_name)
        # coor deal with
        if data['x2'] > im.size[0]:
            data['x2'] = im.size[0]
        if data['y2'] > im.size[1]:
            data['y2'] = im.size[1]
        if data['x'] < 0:
            data['x'] = 0
        if data['y'] < 0:
            data['y'] = 0
        if data['x'] > im.size[0]:
            data['x'] = im.size[0]
        if data['y'] > im.size[1]:
            data['y'] = im.size[1]
        count = 0
        while True:
            try:
                croped = im.crop((data['x'], data['y'], data['x2'], data['y2']))
                break
            except:
                if count > 3:
                    handler = open(Log, 'a')
                    handler.write('-- Crop Error: %s' % source)
                    handler.close()
                    break
                count += 1
                data['y2'] -= 1
                data['x2'] -= 1

        # thumbnail
        # print '(%s, %s), (%s, %s), (%s, %s)' % (data['x'], data['y'], data['x2'], data['y2'], data['w'], data['h'])
        try:
            if abs(data['x2'] - data['x'] - data['w']) > 5 or abs(data['y2'] - data['y'] - data['h']) > 5:
                croped = croped.resize((data['w'],data['h']), Image.BILINEAR)
            croped.save(save);
            # thumb
            croped.thumbnail((227, 403))
            croped.save(save_thumb)
            #  update thumb db
            sql = 'insert into thumb (category, path) values ("%s", "%s")' % (cate, '/%s/%s.jpg' % (cate, pic_name))
            query(db, sql)
        except:
            handler = open(Log, 'a')
            handler.write('-- Save Error: %s' % source)
            handler.close()
    # just update database state
    _src = data['src'].replace('/Upload', '')
    sql = 'update test set state=1 where path="%s"' % _src
    try:
        query(db, sql)
        return True
    except:
        return False

@app.route('/Public/<filename:path>')
def Public(filename):
    '''
    static file
    '''
    return bottle.static_file(filename, root='Public')

@app.route('/Upload/<filename:path>')
def get_image(filename):
    return bottle.static_file(filename, root='/home/thinking/Data/Upload/')

@app.route('/')
def index():
    return bottle.static_file('index.html', root='.')

@app.route('/content/<filename:path>')
def content(filename):
    return bottle.static_file(filename, root='./content/')

@app.route('/cates', method='GET')
def cates(db):
    # sql = 'select distinct category from test where state=0'
    sql = 'select count(`path`) as `count`, `category` from `test` where `state`=0 group by `category`'
    result = query(db, sql)
    if result == None:
        result = []
    # result = [i['category'],  for i in result]
    return json.dumps(result)

@app.route('/_cates', method='GET')
def _cates():
    Home = os.path.expanduser('~') + '/Data'
    Root = '%s/%s' % (Home, 'Temp')
    result = []
    if os.path.exists(Root):
        for cate in os.listdir(Root):
            _path = '%s/%s' % (Root, cate)
            if not os.path.isdir(_path):
                continue
            result.append(cate)
    return json.dumps(result)

@app.route('/cate', method='GET')
def cate(db):
    cate = request.params['cate'].strip()
    start = 0
    step = 20
    try:
        start = int(request.params['start'].strip())
    except:
        start = 0
    sql = 'select path from test where state=0 and category="%s" limit %s,%s' % (cate, start, step)
    # sql = 'select path from test where state=0 and category="%s"' % cate
    res = query(db, sql)
    result = {'caterogy': cate}
    if res == None:
        res = []
    result['data'] = [i['path'] for i in res]
    return result

@app.route('/skip', method='POST')
def skip(db):
    try:
        src = request.params['src'].replace('/Upload', '')
        sql = 'update test set state=2 where path="%s"' % src
        query(db, sql)
        return 'True'
    except:
        return 'Failed'

@app.route('/crop', method='POST')
def crop(db):
    coor = dict()
    coor['x'] = int(round(float(request.params['x'])))
    coor['y'] = int(round(float(request.params['y'])))
    coor['x2'] = int(round(float(request.params['x2'])))
    coor['y2'] = int(round(float(request.params['y2'])))
    coor['w'] = int(round(float(request.params['w'])))
    coor['h'] = int(round(float(request.params['h'])))
    coor['cate'] = request.params['cate']
    coor['src'] = request.params['src']
    coor['crop'] = request.params['crop']
    if _crop(db, coor):
        return 'success'
    else:
        return 'Failed'

################################################################################
# thumb
################################################################################
@app.route('/r_cates', method='GET')
def r_cates(db):
    # sql = 'select distinct category from test where state=0'
    sql = 'select count(`path`) as `count`, `category` from `thumb` where `state`=0 group by `category`'
    result = query(db, sql)
    if result == None:
        result = []
    return json.dumps(result)

@app.route('/r_cates2', method='GET')
def r_cates2(db):
    sql = 'select distinct `category` from `thumb`'
    result = query(db, sql)
    if result == None:
        result = []
    result = [i['category'] for i in result]
    return json.dumps(result)

@app.route('/r_cate', method='GET')
def r_cate(db):
    cate = request.params['cate'].strip()
    start = 0
    step = 100
    try:
        start = int(request.params['start'].strip())
    except:
        start = 0
    sql = 'select path from thumb where state=0 and category="%s"' % (cate)
    # sql = 'select path from thumb where state=0 and category="%s" limit %s,%s' % (cate, start, step)
    # sql = 'select path from test where state=0 and category="%s"' % cate
    res = query(db, sql)
    result = {'caterogy': cate}
    if res == None:
        res = []
    result['data'] = [i['path'] for i in res]
    return result

@app.route('/r_stat', method='GET')
def r_stat(db):
    sql = 'select count(*) as count from thumb where state=0 or state=1'
    res = query(db, sql)
    return json.dumps(res[0])


@app.route('/r_move', method='POST')
def r_move(db):
    media = {}
    media['n_cate'] = request.params['cate'].strip()
    media['subfix'] = request.params['path']
    media['cate'] = media['subfix'][1:].split('/', 1)[0]
    media['name'] = media['subfix'].rsplit('/', 1)[-1]
    if media['cate'] == media['n_cate']:
        return 'nothing to do'
    media['n_subfix'] = '/%s/%s' % (media['n_cate'], media['name'])
    Home = os.path.expanduser('~') + '/Data'
    Store = '%s/Temp' % Home
    Thumb = '%s/Thumb' % Home

    if not os.path.exists('%s%s' % (Store, media['subfix'])):
        return 'file not exists'
    if media['n_cate'] == '':
        Trash = '%s/Trash' % Home
        if not os.path.exists(Trash):
            os.mkdir(Trash)
        os.rename('%s/%s' % (Store, media['subfix']), '%s/%s' % (Trash, media['name']))
        sql = 'update thumb set state=2 where path="%s"'
        query(db, sql % media['subfix'])
        return 'droped'
    if not os.path.exists('%s/%s' % (Store, media['n_cate'])):
        os.mkdir('%s/%s' % (Store, media['n_cate']))
    if not os.path.exists('%s/%s' % (Thumb, media['n_cate'])):
        os.mkdir('%s/%s' % (Thumb, media['n_cate']))
    os.rename('%s%s' % (Store, media['subfix']), '%s%s' % (Store, media['n_subfix']))
    if not os.path.exists('%s%s' % (Thumb, media['subfix'])):
        im = Image.open('%s%s' % (Store, media['n_subfix']))
        im.thumbnail((227, 403))
        im.save('%s%s' % (Thumb, media['n_subfix']))
    else:
        os.rename('%s%s' % (Thumb, media['subfix']), '%s%s' % (Thumb, media['n_subfix']))
    sql = 'update thumb set path="%s", category="%s"  where path="%s"' % (media['n_subfix'], media['n_cate'], media['subfix'])
    query(db, sql)
    return 'success'

@app.route('/r_merge', method='POST')
def r_merge(db):
    if 'from' not in request.params.keys() and 'to' not in request.params.keys():
        return 'from where to where?'
    _from_cate = request.params['from']
    _to_cate = request.params['to']
    if _from_cate == _to_cate:
        return 'from self to self'
    Home = os.path.expanduser('~') + '/Data'
    Temp = '%s/Temp' % (Home)
    Thumb = '%s/Thumb' % Home
    _from = '%s/%s' % (Temp, _from_cate)
    _to = '%s/%s' % (Temp, _to_cate)
    _from_thumb = '%s/%s' % (Thumb, _from_cate)
    _to_thumb = '%s/%s' % (Thumb, _to_cate)

    # update database: rename category, rewrite path
    sql = 'select id, path from thumb where category="%s"' % _from_cate
    sql_2 = 'update thumb set path="%s" where id=%s'
    for i in query(db, sql):
        i['path'] = '/%s%s' % (_to_cate, i['path'][i['path'].rfind('/'):])
        query(db, sql_2 % (i['path'], i['id']))
    sql_3 = 'update thumb set category="%s" where category="%s"' % (_to_cate, _from_cate)
    query(db, sql_3)
    
    # move files to correct path
    # check if exists, then use shell command to move
    os.system('mkdir -p %s && mv %s/* %s && rmdir %s' % (_to, _from, _to, _from))
    os.system('mkdir -p %s && mv %s/* %s && rmdir %s' % (_to_thumb, _from_thumb, _to_thumb, _from_thumb))

    return 'success'


@app.route('/r_tar', method='POST')
def r_tar(db):
    if 'cate' not in request.params.keys():
        return 'no cate selected'
    cate = request.params['cate'].strip()
    # mv files
    Home = os.path.expanduser('~') + '/Data'
    Temp = '%s/Temp' % (Home)
    Fin = '%s/Fin/%s' % (Home, datetime.datetime.now().date())
    _from = '%s/%s' % (Temp, cate)
    _to = '%s/%s' % (Fin, cate)
    if not os.path.exists(_from):
        return '%s not exist' % cate
    if not os.path.exists(_to):
        os.makedirs(_to)
    sql = 'update thumb set state=1 where path="%s"'
    for item in os.listdir(_from):
        try:
            os.rename('%s/%s' % (_from, item), '%s/%s' % (_to, item))
            subfix = '/%s/%s' % (cate, item)
            query(db, sql % subfix)
        except:
            continue
    # send mail
    print 'Sending mail'
    subject = 'IOS7壁纸分类%s 已处理' % cate
    body = '分类 %s 已处理，可以上传。<br />路径: %s' % (cate, _to)
    #_to = ['chinaxiahaifeng@gmail.com']
    _to = ['chinaxiahaifeng@gmail.com']
    mail(_to, subject, body)
    # update database
    return 'success'

run(app, host='127.0.0.1', port=8080)
# end
