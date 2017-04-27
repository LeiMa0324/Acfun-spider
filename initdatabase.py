import pymysql
dbconfig = {}

with open("dbconfig.txt", "rb") as config:

    con = config.readlines()
    dbconfig["ip"] = con[0].replace("ip=", "").replace("\r\n", "").replace("\n","")
    dbconfig["user"] = con[1].replace("user=", "").replace("\r\n", "").replace("\n","")
    dbconfig["passwd"] = con[2].replace("passwd=", "").replace("\r\n", "").replace("\n","")
    dbconfig["db"] = con[3].replace("db=", "").replace("\r\n", "").replace("\n","")
    dbconfig["maxid"] = con[4].replace("maxid=", "").replace("\r\n", "").replace("\n","")

print(dbconfig)



conn = pymysql.connect(host=dbconfig["ip"], user=dbconfig["user"], passwd=dbconfig["passwd"],
                       charset='utf8')
try:
    cur = conn.cursor()
    conn.select_db(dbconfig["db"])
    #创建数据库
    with open("sql/acfun_table.sql", "rb") as au:
        ausql = au.read()
    cur.execute(ausql)
    conn.commit()

    # 创建用户表
    with open("sql/acfun_user.sql", "rb") as au:
        ausql = au.read()
    cur.execute(ausql)
    conn.commit()
    #  创建视频表
    with open("sql/acfun_video.sql", "rb") as av:
        avsql = av.read()
    cur.execute(avsql)
    # 创建tag 表
    with open("sql/acfun_tag.sql", "rb") as at:
        atsql = at.read()
    cur.execute(atsql)
    conn.commit()

except Exception, e:
    print e
finally:
    conn.close()