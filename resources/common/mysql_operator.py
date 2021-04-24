import pymysql
import time
from dbutils.pooled_db import PooledDB
from .logger import get_logger

logger=get_logger(name="mysqlOperator",log_file="logs/logger.log")

class MysqlPool():
    def __init__(self,host,user,password,db):
        self.POOL=PooledDB(
            creator=pymysql,
            maxconnections=10,
            mincached=3,
            maxcached=5,
            blocking=True,
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db,
            charset='utf8'
        )
    
    
    def connect(self):
        """
        启动连接
        """
        conn=self.POOL.connection()
        cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
        return conn,cursor
    
    def closeConn(self,conn,cursor):
        cursor.close()
        conn.close()
    
    def fetchOne(self,sqlStr,args):
        """
        查询一条
        """
        logger.info("%s,args:%s",sqlStr,args)
        result=None
        try:
            conn,cursor=self.connect()
            cursor.execute(sqlStr,args)
            result=cursor.fetchone()
        except Exception as e:
            logger.error("fetchOne error",exc_info=True)
        finally:
            self.closeConn(conn,cursor)
            return result
    
    def fetchAll(self,sqlStr,args):
        """
        查询所有数据
        """
        logger.info("%s,args:%s",sqlStr,args)
        result=None
        try:
            conn,cursor=self.connect()
            cursor.execute(sqlStr,args)
            result=cursor.fetchall()
        except Exception as e:
            logger.error("fetchAll error",exc_info=True)
        finally:
            self.closeConn(conn,cursor)
            return result
    
    def insert(self,sqlStr,args):
        """
        插入数据
        """
        logger.info("%s,args:%s",sqlStr,args)
        row=0
        try:
            conn, cursor = self.connect()
            row = cursor.execute(sqlStr, args)
            logger.info("insert %s records!",row)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("insert error",exc_info=True)
        finally:
            self.closeConn(conn, cursor)
            return row
        
class AiBiDbOperator():
    """
    db:nc_ai_bi
    """
    def __init__(self, host, user, passwd, db):
        # 连接mysql
        self.mysqlPool=MysqlPool(host,user,passwd,db)
    
    def insertUpdateIDInfo(self,userId,schoolName,info):
        """
        插入信息至tbl_student_basic_info
        info:{"name","gender","nation","birth","address","idNumber"}/{"validity"}
        """
        row=0
        #判断正反面
        if "validity" in info.keys():
            insertStr="insert into tbl_student_basic_info(student_id,college,id_validity) values(%s,%s,%s) ON DUPLICATE KEY UPDATE \
                college=VALUES(college),id_validity=VALUES(id_validity)"
            row=self.mysqlPool.insert(insertStr, (userId, schoolName, info["validity"]))
        else:
            insertStr="insert into tbl_student_basic_info(student_id,student_name,college,gender,birthday,id_number,nation,address) values(%s,%s,%s,%s,%s,%s,%s,%s) \
            ON DUPLICATE KEY UPDATE student_name=values(student_name),college=values(college),gender=values(gender),\
            birthday=values(birthday),id_number=values(id_number),nation=values(nation),address=values(address)"
            row=self.mysqlPool.insert(insertStr, (userId, info["name"], schoolName,info["gender"], info["birth"],info["idNumber"],info["nation"],info["address"]))
        if row>0:
            return True
        else:
            return False
    
    def insertUpdateStudentInfo(self,userId,schoolName,info):
        """
        将学生信息插入tbl_student_basic_info
        """
        #先解析info
        fields={"name":"","gender":"","studentNumber":"","major":"","academy":""}
        for key in fields.keys():
            if key in info:
                fields[key]=info[key]

        insertStr="insert into tbl_student_basic_info(student_id,student_name,college,gender,student_number,major,academy) values(%s,%s,%s,%s,%s,%s,%s)\
            ON DUPLICATE KEY UPDATE student_number=values(student_number),major=values(major),academy=values(academy)"
        row=self.mysqlPool.insert(insertStr,[userId,fields["name"],schoolName,fields["gender"],fields["studentNumber"],fields["major"],fields["academy"]])
    
    def insertUpdateImageInfo(self,userId,serverHost,imagePath,imageName,imageLabel,imageType,recoText="",faceLocations=""):
        """
        插入信息至tbl_student_image_info
        """
        insertStr="insert into tbl_student_image_info(student_id,image_addr,image_path,image_name,image_label,image_type,reco_result,face_locations) values(%s,%s,%s,%s,%s,%s,%s,%s)"
        row=self.mysqlPool.insert(insertStr,[userId,serverHost,imagePath,imageName,imageLabel,imageType,recoText,faceLocations])
        if row>0:
            return True
        else:
            return False
    
    def insertUpdateBasicInfo(self,userId,studentName,gender,birthday,schoolName,lng,lat):
        insertStr="insert into tbl_student_basic_info(student_id,student_name,college,gender,birthday,lng,lat) values(%s,%s,%s,%s,%s,%s,%s)\
            ON DUPLICATE KEY UPDATE student_name=values(student_name),college=values(college),gender=values(gender),birthday=values(birthday),lng=values(lng),lat=values(lat)"
        row=self.mysqlPool.insert(insertStr,[userId,studentName,schoolName,gender,birthday,lng,lat])

    def selectCheckInfo(self,userId):
        """
        查询需要校验的字段:name,gender,birthday,college
        """
        queryStr="select student_name,gender,birthday,college from tbl_student_basic_info where student_id=%s"
        row=self.mysqlPool.fetchOne(queryStr,(userId))
        return row
    
    def insertCheckInfo(self,checkInfo):
        """
        将校验结果插入name,gender至tbl_student_info_check
        """
        insertStr="insert into tbl_student_info_check(student_id,old_value,new_value,check_field,check_type) \
        values(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE old_value=values(old_value),new_value=values(new_value)"
        self.mysqlPool.insert(insertStr,checkInfo)

    

