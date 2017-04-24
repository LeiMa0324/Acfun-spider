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


def Spider(mid):
    #获取用户数据
    UPUser = ACrequests.userRequest(mid)
    if UPUser:

        pagenum=1
        VideoList=[]
        #获取第一页视频列表
        soup = ACrequests.VideoListRequest(mid,pagenum)
        pageList = eval(soup.body.text.replace("true","True").replace("false","False"))

        #视频数不为0时，遍历每一页
        if pageList["data"]["page"]["totalCount"]!=0:
            avListPerpage = soup.find_all("a")

            for i in avListPerpage:
                VideoList.append(i.get("href").replace("'" , "").replace("\\","").replace("\"",""))

            while pageList["data"]["page"]["pageNo"]!=pageList["data"]["page"]["totalPage"]:
                print "pageNo:%d and totalPage:%d" %( pageList["data"]["page"]["pageNo"],pageList["data"]["page"]["totalPage"])
                pagenum += 1
                print pagenum
                soup = ACrequests.VideoListRequest(mid,pagenum)
                avListPerpage = soup.find_all("a")
                pageList = eval(soup.body.text.replace("true","True").replace("false","False"))
                print avListPerpage
                for j in avListPerpage:
                    VideoList.append(j.get("href").replace("\\","").replace("\"",""))

            print "用户%d共有%d条视频"% (mid,len(VideoList))
            #获取视频详细信息
            VideoDetaiList=[]
            for v in VideoList:
                VideoDetail = dict(ACrequests.VideoDetailRequest(v),**ACrequests.contentRequest(v))
                taglist = ACrequests.tagsRequest(v)
                if taglist:
                    tagstr=""
                    tagIdlist=[]
                    for tag in taglist:
                        tagIdlist.append(str(tag["tagId"]))
                    VideoDetail["tags"]=",".join(tagIdlist)
                else:
                    VideoDetail["tags"]=""
                VideoDetaiList.append(VideoDetail)

            '''
            插入用户、视频数据与tag数据
            '''
        else:
            "用户视频数量为0"
















    # UPUserstr=pattern.match(userinfo).group(2)
    # UPUser=eval(UPUserstr)
    # print UPUser
GetVideoList("4177720")

