import cv2
import time
import numpy as np
from .card_detect import detectCard,CARDTPYE
from .face_detect import *
from .common.config_parse import ConfigParser
from .common.mysql_operator import AiBiDbOperator
from .common.logger import get_logger
from .common.utils import *
from .common.tools import *
from PIL import Image

logger=get_logger(name="processMain",log_file="logs/logger.log")
configParser=ConfigParser()
dbOperator=AiBiDbOperator(configParser.mysql["host"],configParser.mysql["user"],configParser.mysql["pwd"],configParser.mysql["db1"])


def processMain(imageData,userId,proType,**kwargs):
    """
    params:
        imageData:base64图像数据
        userId：
        proType:过程类型ID(0)/FACE(1)/STUDENT(2)
        imageLabel:正反面
        schoolName:高校名称
        imageOrientation:图像旋转
        faceLandmarks:人脸特征点[(x1,y1),(x2,y2),...]
    """
    #将图像转为opencv image
    #image=base64ToCvImage(imageData,imageOrientation)
    image=imageFileToCvImage(imageData)
    if proType==0:
        return processIdImage(image,userId,kwargs["imageLabel"],kwargs["schoolName"])
    elif proType==1:
        return processFaceImage(image,userId,kwargs["faceLandmarks"])
    elif proType==2:
        return processStudentImage(image,userId,kwargs["schoolName"],kwargs["imageLabel"])

def processIdImage(image,userId,imageLabel,schoolName):
    """
    app上传的图片处理流程：
    1)先上传身份证:ocr识别->提取信息存储->图片存储->返回结果
    params:
        image:app上传的图片
        userId:app生成的用户id
        imageLabel:图片正反面：0表示正面，1表示反面，无正反默认1
        schoolName:学校名称
    """
    try:
        #先提取图片信息
        info=detectCard(image,CARDTPYE.ID,imageLabel)
        #存储图片信息
        imagePath,imageName=saveImage(image,configParser.filePath,userId,"I",imageLabel)
        ret1=dbOperator.insertUpdateIDInfo(userId,schoolName,info)
        ret2=dbOperator.insertUpdateImageInfo(userId,configParser.serverHost,imagePath,imageName,imageLabel,"I",recoText=info["recoText"])
        logger.info("processIdImage run success!")
        if ret1 and ret2:
            return True
        else:
            return False
    except Exception as e:
        logger.error("processIdImage",exc_info=True)
        return False

def processFaceImage(image,userId,faceLandmarks):
    """
    2)上传人脸:特征存储->图片存储->返回结果
    """
    faceLocations=face_recognition.face_locations(image)
    imagePath,imageName=saveImage(image,configParser.filePath,userId,"F",1)
    dbOperator.insertUpdateImageInfo(userId,configParser.serverHost,imagePath,imageName,1,"F",recoText=faceLandmarks,faceLocations=str(faceLocations))
    return True

def processStudentImage(image,userId,schoolName,imageLabel):
    """
    3)上传学生卡:ocr识别->提取信息存储->与id卡信息进行对比->图片存储->返回认证结果
    """
    try:
        cardType=getCardType("config/school.json",schoolName)
        logger.info("input schoolName:%s,cardType:%s",schoolName,cardType)
        info=detectCard(image,CARDTPYE[cardType])
        retInfo={}
        #存储图片信息
        imagePath,imageName=saveImage(image,configParser.filePath,userId,"S",imageLabel)
        dbOperator.insertUpdateImageInfo(userId,configParser.serverHost,imagePath,imageName,imageLabel,"S",recoText=info["recoText"])
        #校验学生卡与id卡信息
        checkInfo=dbOperator.selectCheckInfo(userId)
        if checkInfo is not None:
            if checkInfo["student_name"]!=info["name"]:
                #checkResult.append((userId,checkInfo["student_name"],info["name"],"student_name",0))
                dbOperator.insertCheckInfo((userId,checkInfo["student_name"],info["name"],"student_name",0))
                #避免更新
                if checkInfo["student_name"]!="":
                    info["name"]=checkInfo["student_name"]
                else:
                    checkInfo["student_name"]=info["name"]
            if "gender" in info.keys() and checkInfo["gender"]!=info["gender"]:
                #checkResult.append((userId,checkInfo["gender"],info["gender"],"gender",0))
                dbOperator.insertCheckInfo((userId,checkInfo["gender"],info["gender"],"gender",0))
                #避免更新
                if checkInfo["gender"]!="":
                    info["gender"]=checkInfo["gender"]
                else:
                    checkInfo["gender"]=info["gender"]
            
        #更新学生卡信息
        dbOperator.insertUpdateStudentInfo(userId,schoolName,info)
        
        #返回需要校验的字段
        retInfo["studentName"]=checkInfo["student_name"]
        retInfo["gender"]=checkInfo["gender"]
        retInfo["birthday"]=checkInfo["birthday"]
        retInfo["schoolName"]=schoolName
        logger.info("processStudentImage run success!")
        return retInfo
    except Exception as e:
        logger.error("processStudentImage",exc_info=True)
        return None

def saveCheckedInfo(userId,studentName,gender,birthday,schoolName,lng,lat):
    """
    存储用户校验后的数据，并与ocr数据进行对比
    """
    try:
        checkInfo=dbOperator.selectCheckInfo(userId)
        if checkInfo is not None:
            if checkInfo["student_name"]!=studentName:
                dbOperator.insertCheckInfo((userId,checkInfo["student_name"],studentName,"student_name",1))
            if checkInfo["gender"]!=gender:
                dbOperator.insertCheckInfo((userId,checkInfo["gender"],gender,"gender",1))
            if checkInfo["birthday"]!=birthday:
                dbOperator.insertCheckInfo((userId,checkInfo["birthday"],birthday,"birthday",1))
            if checkInfo["college"]!=schoolName:
                dbOperator.insertCheckInfo((userId,checkInfo["college"],schoolName,"college",1))
        dbOperator.insertUpdateBasicInfo(userId,studentName,gender,birthday,schoolName,lng,lat)
        logger.info("saveCheckedInfo run success!")    
    except Exception as e:
        logger.error("saveCheckedInfo",exc_info=True)

def processApprovalStudentInfo(userId,birthday,schoolName):
    """
    审批学生信息：
    1)计算年龄
    2)判断学校
    3)计算人脸相似度
    4)核对信息校验项,存在多少项不一致
    """



