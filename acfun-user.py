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
    tuple =ACrequests.userRequest(uid)
    try:
        #返回用户成功
        if type(tuple) !=int:
            upuser =tuple[1]
            pagecount = tuple[2]
            pagenum=1
            #获取第一页视频列表
            soup = ACrequests.VideoListRequest(uid,pagenum)
            pageList = json.loads(soup.body.text)

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

                pageinfo = json.loads( str(soup.find(text=re.compile("pageNo.*(\d*)")))+'"}}')

                while pageinfo["data"]["page"]["pageNo"]!=pageinfo["data"]["page"]["totalPage"]:
                    pagenum += 1
                    soup = ACrequests.VideoListRequest(uid,pagenum)
                    avListPerpage = soup.find_all("a")
                    pageinfo =  json.loads(
                        str(soup.find(text=re.compile("pageNo.*(\d*)"))) + '"}}')

                    for j in avListPerpage:
                        VideoList.append(j.get("href").replace("\\","").replace("\"",""))

                print "用户%s共有%d条视频"% (uid,len(VideoList))

                for v in VideoList:

                    # 检查返回值，区别对待
                    vDetail = ACrequests.VideoDetailRequest(v)
                    if vDetail:
                        VideoDetail = dict(vDetail,**ACrequests.contentRequest(v))
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
                print "该用户没有视频%s" %uid
                insert2DB(upuser,pagecount)
        else:
            print "用户获取失败！%s" % uid
    except Exception,e:
        print e
        print uid
        traceback.print_exc(file=sys.stdout)
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

def insert2DB(upuser,pagecount,VideoDetaiList=[],tagList=[]):

     conn = pymysql.connect(host=dbconfig["ip"], user=dbconfig["user"], passwd=dbconfig["passwd"],
                            charset='utf8')
     try:
         cur = conn.cursor()
         conn.select_db(dbconfig["db"])

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
             conn.commit()
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
             '''
             去除重复项
             '''
             for tag in tagList:
                 while tagList.count(tag) > 1:
                     del tagList[tagList.index(tag)]
             print "该用户共tag%d条" % len(tagList)

             tagnum= 0
             tagrepeated = 0
             for tag in tagList:
                 # 检查tag是否已存在
                 cur.execute("select count(*) from acfun_tag where tagId=%s" % tag["tagId"])
                 record = cur.fetchone()[0]
                 if record == 1:
                     tagrepeated += 1
                 else:
                     sql= 'INSERT INTO acfun_tag VALUES (%s,%s,%s)'
                     tmp = [tag["tagId"],tag["tagName"],tag["refCount"]]
                     cur.execute(sql,tmp)
                     conn.commit()
                     tagnum +=1
             print "tag 存储成功！共有%d条已有tag，存入%d条tag" % (tagrepeated,tagnum)

     except Exception, e:
         print e
     finally:
         conn.close()

#检查数据库中最后一条记录
def lastuserindb():
      conn = pymysql.connect(host=dbconfig["ip"], user=dbconfig["user"], passwd=dbconfig["passwd"], charset='utf8')
      lastuser=[0]
      try:

          cur = conn.cursor()
          # cur.execute('create database if not exists python')
          conn.select_db(dbconfig["db"])
          #检查是否该用户已存在
          cur.execute("select max(id) from acfun_user;")
          lastuser[0] = cur.fetchone()[0]

      except Exception,e:
        print e
      finally:
          #关闭数据库
        conn.close()
        if lastuser[0] :
            lastuser[0]=lastuser[0]
        else:
            lastuser[0]=0
        return  lastuser[0]

def multiprocessingSpider(uids):
    #开启4个线程
    pool = ThreadPool(4)
    try:
        results = pool.map(Spider, uids)

    except Exception, e:
        # print 'ConnectionError'
        print e
        #用map函数代替for循环，开启多线程运行函数
        results = pool.map(Spider, uids)

    pool.close()
    pool.join()


'''
主程序
'''
dbconfig = {}
with open("dbconfig.txt", "rb") as config:
    con = config.readlines()
    dbconfig["ip"] = con[0].replace("ip=", "").replace("\r\n", "").replace("\n","")
    dbconfig["user"] = con[1].replace("user=", "").replace("\r\n", "").replace("\n","")
    dbconfig["passwd"] = con[2].replace("passwd=", "").replace("\r\n", "").replace("\n","")
    dbconfig["db"] = con[3].replace("db=", "").replace("\r\n", "").replace("\n","")
    dbconfig["maxid"] = con[4].replace("maxid=", "").replace("\r\n", "").replace("\n","")
    dbconfig["limitid"] = con[4].replace("limitid=", "").replace("\r\n", "").replace("\n", "")

print(dbconfig)


count=[0]
'''
40万，最早视频是2013/02/23
8629119我自己，注册时间 2016年12月6日
'''
lastuser =lastuserindb()

#选择数据库和文件中最大值
maxid=int(dbconfig["maxid"]) if int(dbconfig["maxid"])>int(lastuserindb()) else int(lastuserindb())
print"当前数据库中最大用户为：", maxid


# 一次获取100w个用户
for m in range(0,9999):
    uids = []
    if  dbconfig["limitid"]>maxid+(m+1)*100:
        for i in range(maxid+m*100,maxid+(m+1)*100 ):
             uids.append(str(i))
        multiprocessingSpider(uids)
    else:
        for i in range(maxid+m*100,dbconfig["limitid"]+1 ):
             uids.append(str(i))

        break









