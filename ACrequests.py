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
import ast


dbconfig = {}

with open("dbconfig.txt", "rb") as config:

    con = config.readlines()
    dbconfig["ip"] = con[0].replace("ip=", "").replace("\r\n", "").replace("\n","")
    dbconfig["user"] = con[1].replace("user=", "").replace("\r\n", "").replace("\n","")
    dbconfig["passwd"] = con[2].replace("passwd=", "").replace("\r\n", "").replace("\n","")
    dbconfig["db"] = con[3].replace("db=", "").replace("\r\n", "").replace("\n","")
    dbconfig["maxid"] = con[4].replace("maxid=", "").replace("\r\n", "").replace("\n","")

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
#请求用户信息
def userRequest(mid):
    url="http://www.acfun.cn/u/%s.aspx" % mid
    ua=random.choice(uas)
    head["User-Agent"]=ua
    response=requests.get(url,headers=head)
    print "__________________________________________________________________"
    print "请求用户中.."
    if response.status_code==200:
        print "用户请求成功%s" % mid
        html = response.content
        soup = BeautifulSoup(html,"lxml")
        userinfo = soup.select(".main")[0].next.text
        pattern = re.compile("(.*?)=(.*)$",re.M)
        list = pattern.findall(userinfo)

        upuser = json.loads(list[0][1])
        pagecount= json.loads(list[2][1])


        return response.status_code,upuser,pagecount
    else:
        if response.status_code==404:
            print "用户不存在"
        else:
            if response.status_code ==403:

               print "请求失败"
               '''
                存入数据库
                '''
        print "请求用户%s失败，错误码%s"%(mid,response.status_code)
        return response.status_code

#请求某个用户的，某一页的所有视频
def VideoListRequest(mid,pagenum):
    ua=random.choice(uas)
    head["User-Agent"]=ua
    url="http://www.acfun.cn/space/next?uid=%s&type=video&orderBy=2&pageNo=%s" %(mid,pagenum)
    response=requests.get(url,headers=head)
    if response.status_code==200:
        return BeautifulSoup(response.content,"lxml")
    else:

        print response.status_code
        '''
        讨论403与404
        '''


#请求单个视频具体信息
def VideoDetailRequest(vid):
    url="http://www.acfun.cn"+vid
    ua=random.choice(uas)
    head["User-Agent"]=ua
    response = requests.get(url,headers=head)

    if response.status_code==200:
        html=response.content
        #视频被删除
        pattern =re.compile("error")
        search = pattern.search(response.url)
        if search:
            print "视频错误"
        else:

            if response.url=="http://www.acfun.cn"+"/a/"+vid.replace("/v/",""):
                saveFailVideo(vid.replace("/v/ac",""),"0")
            else:
                soup=BeautifulSoup(html,"lxml")
                pageInfo = soup.find("script",text=re.compile("var pageInfo")).text.replace("var pageInfo =","")
                pageInfoDict =  json.loads(pageInfo)
                VideoDetail={}
                #发布时间
                VideoDetail["id"] = vid.replace("/v/ac","")
                VideoDetail["contributeTime"]=pageInfoDict["contributeTime"]
                #视频名称
                VideoDetail["title"] = pageInfoDict["title"]
                #视频描述
                VideoDetail["description"] = pageInfoDict["description"]
                #时长
                VideoDetail["duration"]=pageInfoDict["duration"]
                #投蕉数
                VideoDetail["banana"] = pageInfoDict["bananaCount"]

                return VideoDetail
    else:
        print "请求视频详情失败，%d" % response.status_code
        saveFailVideo(vid.replace("/v/ac", ""), "1")

#请求某个视频所有tag的json，成功，返回taglist，不成功，不返回
def tagsRequest(vid):
    url = "http://www.acfun.cn/member/collect_up_exist.aspx?contentId="+vid.replace("/v/ac","")
    response = requests.get(url,headers=head)
    if response.status_code==200:
        taglistdict =json.loads( response.text)
        return taglistdict["data"]["tagList"]

    else:
        print "请求tag失败"

#请求视频的几个number
def contentRequest(vid):
    url="http://www.acfun.cn/content_view.aspx?contentId="+vid.replace("/v/ac","")
    ua=random.choice(uas)
    head["User-Agent"]=ua
    response = requests.get(url,headers=head)
    if response.status_code==200:
        contentDict={}
        contentlist = json.loads( response.text)
        contentDict["playnum"] = contentlist[0]
        contentDict["commentnum"] = contentlist[1]
        contentDict["bulletnum"] = contentlist[4]
        contentDict["favoritenum"] = contentlist[5]
        return contentDict
    else:
        print "请求content失败"

# failreason 0-不支持的格式 1-获取视频失败
def saveFailVideo(vid,failreason):
    conn = pymysql.connect(host=dbconfig["ip"], user=dbconfig["user"], passwd=dbconfig["passwd"],
                           charset='utf8')
    try:
        cur = conn.cursor()
        conn.select_db(dbconfig["db"])

        cur.execute("INSERT INTO acfun_fail_video VALUES (%s,%s) " % (vid,failreason))
        conn.commit()
        print "failed video saved！%s"% vid
    except Exception,e:
        print e
    finally:
        conn.close()


# VideoDetailRequest("/v/ac1474943")

