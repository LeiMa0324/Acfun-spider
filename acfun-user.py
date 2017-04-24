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
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    # 'Referer': 'http://space.bilibili.com/45388',
    # 'Origin': 'http://space.bilibili.com',
    # 'Host': 'space.bilibili.com',
    'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
}
def getUserinfo(mid):
    url="http://www.acfun.cn/u/%s.aspx" % mid
    response=requests.get(url,headers=head)
    responseCodeDict = {{"200":success,
                        "403":fail,
                        "404":userdontExist}
    }
    UPUser=responseCodeDict[str(response.status_code)](response,"user")
    #如果用户存在，获取其视频列表
    if UPUser:
        GetVideoList(mid)

def GetVideoList(mid):
    pagenum=1
    VideoList=[]
    #获取第一页视频列表
    soup = VideoRequest(mid,pagenum)
    print soup
    pageList = eval(soup.body.text.replace("true","True").replace("false","False"))
    #视频数不为0时，遍历每一页
    if pageList["data"]["page"]["totalCount"]!=0:
        avListPerpage = soup.find_all("a")
        for i in avListPerpage:
            VideoList.append(avListPerpage.get("href"))

        while pageList["data"]["page"]["prePage"]!=pageList["data"]["page"]["totalPage"]:
            pagenum += 1
            avListPerpage = VideoRequest(mid,pagenum).find_all("a")
            for i in avListPerpage:
                VideoList.append(avListPerpage.get("href"))
    else:
        print "用户：%s视频数为0" %mid
    #获取视频详细信息
    getVideoDetails(VideoList)


def getVideoDetails(VideoList):
    #视频长度不为0
    VideoDetailList=[]
    if VideoList:
        for v in VideoList:
            url="http://www.acfun.cn/content_view.aspx?contentId=3621153"
            response = requests.get(url)
            if response.status_code==200:
                soup=BeautifulSoup(response.content)

                '''
                获取发布时间,mid,投蕉数,uid,时长,title,description
                url="http://www.acfun.cn/v/ac3621153"
                获取tag列表
                url=http://www.acfun.cn/member/collect_up_exist.aspx?contentId=3634816
                获取播放数、评论数、弹幕数、评论数
                url="http://www.acfun.cn/content_view.aspx?contentId=3621153"
                [11543,15,0,0,215,20,57,12]
                播放 评论，xx，xx，弹幕，收藏，xx
                '''
                mid = soup.body.text()

            else:
                print "视频获取失败：%s"% v


def VideoRequest(mid,pagenum):
    url="http://www.acfun.cn/space/next?uid=%s&type=video&orderBy=2&pageNo=%s" %(mid,pagenum)
    print url

    ua=random.choice(uas)
    response=requests.get(url,headers=head)
    responseCodeDict = {"200":success,
                        "403":fail,
                        "404":userdontExist}
    return responseCodeDict[str(response.status_code)](response,"video")

def success(response,userOrvideo):
    if userOrvideo =="user":
        print "用户请求成功"
        html=response.content
        soup=BeautifulSoup(html,"lxml")
        userinfo=soup.select(".main")[0].next.text
        print userinfo
        pattern=re.compile("(.*?)=(.*)$",re.M)
        list=pattern.findall(userinfo)

        UPUser=eval(list[0][1].replace("false","False").replace("true","True"))
        '''
        用户数据插入数据库
        '''
    else:
        '''
        返回soup文件
        '''
        print "视频列表请求成功"
        return BeautifulSoup(response.content)


def fail(response):
    print "403Error"
    '''
    存入数据库
    '''
def userdontExist(response):
    print  "404Error,用户不存在"











    # UPUserstr=pattern.match(userinfo).group(2)
    # UPUser=eval(UPUserstr)
    # print UPUser
GetVideoList("4177720")

