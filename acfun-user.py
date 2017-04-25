# coding=utf-8

import requests
import json
import random
import pymysql
from multiprocessing.dummy import Pool as ThreadPool
from bs4 import BeautifulSoup
import sys
import datetime
import time
from imp import reload
import traceback,sys
from requests.exceptions import ProxyError
import re
import ACrequests

#载入userAgent
def LoadUserAgents(uafile):

    uas = []
    with open(uafile, 'rb') as uaf:
        for ua in uaf.readlines():
            if ua:
                uas.append(ua.strip()[1:-1-1])
    random.shuffle(uas)
    return uas

uas = LoadUserAgents("user_agents.txt")
head = {
    'X-Requested-With': 'XMLHttpRequest',
    # 'Referer': 'http://space.bilibili.com/45388',
    # 'Origin': 'http://space.bilibili.com',
    # 'Host': 'space.bilibili.com',
    'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
}


def Spider(uid):
    #获取用户数据
    (upuser,pagecount) = ACrequests.userRequest(uid)
    if upuser:
        pagenum=1
        #获取第一页视频列表
        soup = ACrequests.VideoListRequest(uid,pagenum)
        pageList = eval(soup.body.text.replace("true","True").replace("false","False"))

        #视频数不为0时，遍历每一页
        if pageList["data"]["page"]["totalCount"]!=0:
            #视频详细信息列表
            VideoDetaiList=[]
            #所有 tag 列表
            tagList=[]
            avListPerpage = soup.find_all("a")
            #视频临时列表
            VideoList = []
            for i in avListPerpage:
                VideoList.append(i.get("href").replace("'" , "").replace("\\","").replace("\"",""))

            pageinfo =eval( str(soup.find(text=re.compile("pageNo.*(\d*)"))).replace("true","True").replace("false","False")+'"}}')

            while pageinfo["data"]["page"]["pageNo"]!=pageinfo["data"]["page"]["totalPage"]:
                print "pageNo:%d and totalPage:%d" %( pageList["data"]["page"]["pageNo"],pageList["data"]["page"]["totalPage"])
                pagenum += 1
                print pagenum
                soup = ACrequests.VideoListRequest(uid,pagenum)
                avListPerpage = soup.find_all("a")
                pageinfo = eval(
                    str(soup.find(text=re.compile("pageNo.*(\d*)"))).replace("true", "True").replace("false",
                                                                                                     "False") + '"}}')

                for j in avListPerpage:
                    VideoList.append(j.get("href").replace("\\","").replace("\"",""))

            print "用户%s共有%d条视频"% (uid,len(VideoList))

            for v in VideoList:
                VideoDetail = dict(ACrequests.VideoDetailRequest(v),**ACrequests.contentRequest(v))
                VideoDetail["uid"]=uid
                #获取每个视频的 taglist
                taglist_per_video = ACrequests.tagsRequest(v)
                if taglist_per_video:
                    tagstr=""
                    tagList.extend(taglist_per_video)
                    tagIdlist=[]
                    for tag in taglist_per_video:
                        tagIdlist.append(str(tag["tagId"]))
                    VideoDetail["tags"]=",".join(tagIdlist)
                else:
                    VideoDetail["tags"]=""
                VideoDetaiList.append(VideoDetail)
            #所有数据插入数据库
            insert2DB(upuser,pagecount,VideoDetaiList,tagList)
        #用户没有视频
        else:
            insert2DB(upuser,pagecount)
    else:
        print "用户获取失败！%s" % uid

def insert2DB(upuser,pagecount,VideoDetaiList=[],tagList=[]):

     conn = pymysql.connect(host=dbconfig["ip"], user=dbconfig["user"], passwd=dbconfig["passwd"],
                            charset='utf8')
     try:
         cur = conn.cursor()
         conn.select_db(dbconfig["db"])
         #创建用户表
         with open("sql/acfun_user.sql", "rb") as au:

             ausql = au.read()
             print ausql
         cur.execute(ausql)
         #  创建视频表
         with open("sql/acfun_video.sql", "rb") as av:

             avsql = av.read()
         cur.execute(avsql)
         # 创建tag 表
         with open("sql/acfun_tag.sql", "rb") as at:

             atsql = at.read()
         cur.execute(atsql)

         '''
         存储用户
         '''
         cur.execute("select count(*) from acfun_user where id=%s", upuser["userId"])

         record = cur.fetchone()[0]
         if record == 1:
             print "用户在数据库中已存在！uid:%s" % upuser["userId"]
         else:
             sql='INSERT INTO acfun_user VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'
             tmp=[upuser["userId"], upuser["username"], upuser["gender"], upuser["signature"], pagecount["video"],
                 pagecount["article"],pagecount["flowed"], pagecount["flow"]]
             # 存入用户表
             cur.execute(sql,tmp)
             print "用户成功存入数据库，uid：", upuser["userId"]
             # 计数
             count[0] += 1
             print "已存入%d个用户" % count[0]

         '''
         存储视频
         '''
         if VideoDetaiList:
             tmp = []
             for i in range(0, len(VideoDetaiList)):
                 data = [VideoDetaiList[i]['id'], VideoDetaiList[i]['uid'],VideoDetaiList[i]['title'], VideoDetaiList[i]['contributeTime'],
                         VideoDetaiList[i]['description'], VideoDetaiList[i]['duration'],
                         VideoDetaiList[i]['banana'], VideoDetaiList[i]['playnum'], VideoDetaiList[i]['commentnum'],
                         VideoDetaiList[i]['bulletnum'], VideoDetaiList[i]['favoritenum'],
                         VideoDetaiList[i]['tags']]
                 tmp.append(data)
             cur.executemany(
                 'INSERT INTO acfun_video VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                 tmp)
             conn.commit()
             print "视频存储成功！"
         '''
         存储 tag
         '''
         if tagList:
             for tag in tagList:
                 # 检查tag是否已存在
                 print tag
                 cur.execute("select count(*) from acfun_tag where tagId=%s" % tag["tagId"])
                 record = cur.fetchone()[0]
                 if record == 1:
                     print "该tag已存在！tagid:%s" % tag["tagId"]
                 else:
                     sql= 'INSERT INTO acfun_tag VALUES (%s,%s,%s)'
                     tmp = [tag["tagId"],tag["tagName"],tag["refCount"]]
                     cur.execute(sql,tmp)


             conn.commit()
             print "tag 存储成功！"

     except Exception, e:
         print e
     finally:
         conn.close()



dbconfig = {}

with open("dbconfig.txt", "rb") as config:

    con = config.readlines()
    dbconfig["ip"] = con[0].replace("ip=", "").replace("\r\n", "").replace("\n","")
    dbconfig["user"] = con[1].replace("user=", "").replace("\r\n", "").replace("\n","")
    dbconfig["passwd"] = con[2].replace("passwd=", "").replace("\r\n", "").replace("\n","")
    dbconfig["db"] = con[3].replace("db=", "").replace("\r\n", "").replace("\n","")
    dbconfig["maxid"] = con[4].replace("maxid=", "").replace("\r\n", "").replace("\n","")

print(dbconfig)


count=[0]

Spider("1715457")







