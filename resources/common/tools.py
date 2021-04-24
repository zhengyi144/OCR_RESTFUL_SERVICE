import json
import requests
import re
import random
import time
import os
import cv2

class IDFeatureCheck():
    def __init__(self,idNumber):
        self.id=idNumber
        self.adcode=int(self.id[0:6])
        self.year=self.id[6:10]
        self.month=self.id[10:12]
        self.day=self.id[12:14]
    
    def getBirthday(self):
        """通过身份证号获取出生日期"""
        return "{0}-{1}-{2}".format(self.year, self.month, self.day)
    
    def getGender(self):
        """通过身份证号获取性别， 女生：0，男生：1"""
        return int(self.id[16:17]) % 2
    
    @staticmethod
    def convertGender(genderStr):
        """
        genderStr:女/男
        return:0/1/""
        """
        if "女" in genderStr:
            return 0
        elif "男" in genderStr:
            return 1
        else:
            return ""
    
    @staticmethod
    def convertBirth(birthStr):
        """
        birthStr:1990年2月3日
        return:1990-02-03
        """
        pattern=re.compile(r"\d{4}年\d{0,2}月\d{0,2}日")
        birthStr=pattern.findall(birthStr)
        if len(birthStr)>0:
            birth=birthStr[0]
            yPattern=re.compile(r"\d{4}(?=年)")
            year=yPattern.findall(birth)[0]
            mPattern=re.compile(r"\d{0,2}(?=月)")
            month=mPattern.findall(birth)[0]
            if len(month)==1:
                month="0"+month
            dPattern=re.compile(r"\d{0,2}(?=日)")
            day=dPattern.findall(birth)[0]
            if len(day)==1:
                day="0"+day
            return "{0}-{1}-{2}".format(year, month,day)
        else:
            return ""        


def loadTxtFile(path):
    """
    按行读取txt
    """
    return [line.strip() for line in open(path, 'r', encoding='UTF-8').readlines()]

def loadJsonFile(path):
    """
    读取yaml文件
    """
    with open(path, 'r', encoding='utf-8') as f:
        fileData = json.load(f)
    return fileData

def postData(url, dataset):
    """
    dataset:{}
    """
    data = json.dumps(dataset)
    # print(merInfoList)
    r = requests.post(url=url, headers={'Content-Type': 'application/json'}, data=data)
    rjson = json.loads(r.text)
    return r, rjson

def makeImagePath(filePath,userId,fileType,imageLabel=0):
    """
    创建图片存储目录:filePath/userId/fileType/imageLabel/*.jpg
    """
    timeStamp=int(round(time.time()*1000))
    path=filePath+"/"+str(userId)+"/"+fileType+"/"+str(imageLabel)
    if not os.path.exists(path):
        os.makedirs(path)
    imageName=str(timeStamp)+".jpg"
    return path,imageName

def saveImage(image,filePath,userId,fileType,imageLabel=0):
    path,imageName=makeImagePath(filePath,userId,fileType,imageLabel)
    imagePath=path+"/"+imageName
    cv2.imwrite(imagePath,image)
    return path,imageName

def getCardType(jsonPath,schoolName):
    schoolDict=loadJsonFile(jsonPath)
    return schoolDict[schoolName]

if __name__=="__main__":
    imagePath=makeImagePath("E:/DATASET/STUDENT",1234568122,"ID")
    print(imagePath)