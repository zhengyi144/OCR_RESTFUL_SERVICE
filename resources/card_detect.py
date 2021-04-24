import cv2
import numpy as np
from enum import Enum
import time
import re
from .common.tools import loadJsonFile,IDFeatureCheck
from .paddle_ocr import *

cardItem=loadJsonFile("./config/cardItem.json")
#print(cardItem)

class CARDTPYE(Enum):
    """
    ID=0 #身份证
	FJNU=1   #福建师范大学
	FJNUXHC=2 #福建师范大学协和学院
	MJU=3 #闽江学院
	FZU=4 #福州大学
	FMU=5 #福建医科大学
	FTCMU=6 #福建中医药大学
	FTU=7 #福建工程学院
	FAAFU=8 #福建农林大学
	MJTC=9    #闽江师范高等专科学校
	FJXC=10 #福建江夏学院
	FTP=11 #福州职业技术学院
    """
    ID=0
    FJNU=1
    FJNUXHC=2
    MJU=3
    FZU=4
    FMU=5
    FTCMU=6
    FTU=7
    FAAFU=8
    MJTC=9
    FJXC=10
    FTP=11

def transDegree(rad):
    return rad/np.pi*180

def calcDeviationAngle(image):
    """
    通过霍夫变换检测文本直线->计算每条直线的倾斜角度(平均值)
    params:
        image:
    """
    if image.ndim<3:
        return
    grayImg=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    edgeImg=cv2.Canny(grayImg,50,200)
    cv2.imshow("edge",edgeImg)
    lines=cv2.HoughLines(edgeImg,1,np.pi/180,80)
    # 依次画出每条线段
    sum=0
    for i in range(len(lines)):
        for rho, theta in lines[i]:
            # print("theta:", theta, " rho:", rho)
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(round(x0 + 1000 * (-b)))
            y1 = int(round(y0 + 1000 * a))
            x2 = int(round(x0 - 1000 * (-b)))
            y2 = int(round(y0 - 1000 * a))
            # 只选角度最小的作为旋转角度
            sum += theta
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 1, cv2.LINE_AA)
            cv2.imshow("Imagelines", image)
    average = sum / len(lines)
    angle = transDegree(average) - 90
    return angle

def rotateImage(image,degree):
    """
    旋转图像
    """
    h,w=image.shape[:2]
    # 计算二维旋转的仿射变换矩阵
    rotateMatrix = cv2.getRotationMatrix2D((w/2.0, h/2.0), degree, 1)
    # 仿射变换，背景色填充为白色
    rotate = cv2.warpAffine(image, rotateMatrix, (w, h), borderValue=(255, 255, 255))
    return rotate

def statiticsHist(image,label=0):
    """
    params:
        image:二值化后的图像
        label:1表示vertical,0表示horizontal
    result:
        hist:二值化直方图
    """
    if image.ndim>=3:
        return
    
    height,width=image.shape
    size=height if label==0 else width
    hist=np.zeros((size,),dtype=int)
    #print(hist.shape)
    for r in range(height):
        for c in range(width):
            if image[r,c]>0:
                if label==0:
                    hist[r]+=1
                else:
                    hist[c]+=1
    return hist

def calFontRows(hist,minSize,maxInterval,minVal=0):
    """
    params:
        hist:直方图
        minSize:row的最小宽度
        minVal:统计直方图value的最小值
        maxInterval:同一行中value=0的最大间隔数
    result:
        rows:各行或者各列的size数组
    """
    rows=[]
    size=0
    interval=0
    length=np.shape(hist)[0]
    for i in range(length):
        if hist[i]>minVal:
            size+=1
            interval=0
        if hist[i]<=minVal:
            if interval<maxInterval and size>0:
                size+=1
                interval+=1
            elif size>minSize:
                rows.append({"index":i+1,"size":size})
                interval=0
                size=0
        if i==length-1 and size>minSize:
            rows.append({"index":i+1,"size":size})
    return rows

def imageProcess(src,rect,threshType,minRSize,maxRInterval,minRVal,minCSize,maxCInterval,minCVal,isAdaptive=True,threshVal=120):
    """
    图像预处理：提取roi区域-->灰度图-->二值化-->形态学处理-->计算直方图-->计算行数-->提取rowImgs
    params:
       src:原始图像
       rect:(x,y,w,h)
       threshType：二值化类型
    result:
        threshImg:处理后的roi区域
    """
    x,y,w,h=rect
    roi=src[y:y+h, x:x+w,:]
    gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
    #cv2.imshow("gray",gray)
    if isAdaptive:
        gray= cv2.GaussianBlur(gray, (5, 5), 0)
        threshImg=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,threshType,7,5)
    else:
        #gray=cv2.medianBlur(gray,3)
        ret,threshImg=cv2.threshold(gray,threshVal,255,threshType)
    cv2.imshow("thresh",threshImg)
    hist=statiticsHist(threshImg)
    #print(hist)
    rows=calFontRows(hist,minRSize,maxRInterval,minRVal)
    #print(rows)
    rowImgs=calcFontRectangle(roi,threshImg,rows,minCSize,maxCInterval,minCVal)
    return rowImgs

def detectMaxBlob(src,rect,threshVal,threshType):
    x,y,w,h=rect
    roiImg=src[y:y+h, x:x+w,:]
    grayImg=cv2.cvtColor(roiImg,cv2.COLOR_BGR2GRAY)
    ret,threshImg=cv2.threshold(grayImg,threshVal,255,threshType)
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    morImg=cv2.morphologyEx(threshImg,cv2.MORPH_ERODE,kernel)
    #cv2.imshow("test",morImg)
    contours,hierarchy=cv2.findContours(morImg,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    maxX=0
    maxY=0
    maxW=0
    maxH=0
    for contour in contours:
        area=cv2.contourArea(contour)
        if area>500:
            (maxX, maxY, maxW, maxH) = cv2.boundingRect(contour)
    if maxW>0 and maxH>0:
        return (int(maxX+maxW+x)+5,int(maxY)+5,180,100)
    return (0,0,0,0)

def calcFontRectangle(src,threshImg,rows,minCSize,maxCInterval,minCVal):
    rowImgs=[]
    h,w=threshImg.shape
    for index,row in enumerate(rows) :
        #print(row)
        rect=(0,row["index"]-row["size"],w,row["size"])
        roi=threshImg[rect[1]:rect[1]+rect[3],rect[0]:rect[0]+rect[2]]
        #cv2.imshow("roi",roi)
        hist=statiticsHist(roi,label=1)
        #print(hist)
        cols=calFontRows(hist,minCSize,maxCInterval,minCVal)
        for c,col in enumerate(cols):
            x=col["index"]-col["size"]-3 if col["index"]-col["size"]-3>0 else 0
            y=rect[1]-3 if rect[1]-3>0 else 0
            trect=(x,y,col["size"],rect[3])
            timg=src[trect[1]:trect[1]+trect[3],trect[0]:trect[0]+trect[2]]
            rowImgs.append(timg)
            cv2.imshow(str(index)+str(c),timg)
    return rowImgs

def splitFontRow(src,dst):
    """
    分割场景：1)身份证地址；2)闽江师专班级
    src参照dst的rows判断是否进行分割
    """
    sh,sw=src.shape[:2]
    dh=src.shape[0]
    times=float(sh)/dh
    rowImgs=[]
    print(times)
    if times>=int(times)+0.6:
        times=int(times)+1
    else:
        times=int(times)
    if times>1:
        y=0
        for i in range(times-1):
            rowImgs.append(src[y:y+dh, :,:])
            y+=dh+3
        rowImgs.append(src[y:sh,:,:])
        return True, rowImgs
    else:
        return False,src

def getItemContent(items,text):
    index=-1
    content=""
    lenght=len(text)
    for item in items:
        index=text.find(item)
        if index!=-1:
            start=index+len(item)
            if start<=lenght:
                content=text[start:lenght]
                break
    return index,content

def getIDFeatureInfo(items,features,recos):
    """
    items:
    recos:[("text",0.9),("text",0.9)]
    return:info={}
    """
    #循环获取feature
    recoLen=len(recos)
    #features=items["features"]
    startIndex=0
    info={}
    for fIndex in range(0,len(features)-1):
        feature=features[fIndex]
        info[feature]=""
        isSplit=False
        isAddress=False
        if feature=="address":
            isAddress=True
        for i in range(startIndex,recoLen):
            reco=recos[i]
            if reco[0][0]!='' and reco[0][1]>0.7:
                if not isSplit:
                    index,content=getItemContent(items[feature],reco[0][0])
                    birth=IDFeatureCheck.convertBirth(reco[0][0])
                    #针对address进行合并,地址首行一定大于9
                    if isAddress:
                        if content!="":
                            info["address"]=content
                        elif (len(reco[0][0])>9 and birth=="") or info["address"]!="": 
                            info["address"]+=reco[0][0]
                        continue

                    if index!=-1 and content!="":
                        info[feature]=content
                        startIndex+=1
                        break
                    elif index!=-1 and content=="":
                        isSplit=True
                else:
                    if feature=="name":
                        index,content=getItemContent(items["gender"],reco[0][0])
                        if index==-1 and IDFeatureCheck.convertGender(reco[0][0])=="":
                            info["name"]=reco[0][0]
                            startIndex+=1
                    elif feature=="gender":
                        gender=IDFeatureCheck.convertGender(reco[0][0])
                        if gender!="":
                            info["gender"]=gender
                            startIndex+=1
                    elif feature=="nation":
                        index,content=getItemContent(items["birth"],reco[0][0])
                        if index==-1:
                            info["nation"]=reco[0][0]
                            startIndex+=1
                    elif feature=="birth":
                        birth=IDFeatureCheck.convertBirth(reco[0][0])
                        if birth!="":
                            info["birth"]=birth
                            startIndex+=1
                    break 
    return info

def getStudentCardInfo(rowImgs,schoolLabel):
    """
    针对干扰信息较少的学生卡,进行统一处理方式
    """
    recoText=""
    recos=[]
    for img in rowImgs:
        reco=OCR.ocr(img,det=False,rec=True)
        text=reco[0][0]
        recoText+=text+";"
        if text!='' and reco[0][1]>0.7:
            recos.append(text)
    #循环遍历各个属性 
    info={}
    items=cardItem["ITEMS"]
    features=cardItem[schoolLabel]["features"] 
    for feature in features:
        info[feature]=""
        for text in recos:
            index,content=getItemContent(items[feature],text)
            if index!=-1:
                recos.remove(text)
                if "：" in content:
                    content=content.replace("：","")
                if feature=="studentNumber":
                    pattern=re.compile(r"[a-zA-Z0-9]+")
                    result = pattern.findall(content)
                    if result is not None and len(result)>0:
                        info[feature]=result[0]     
                else:
                    info[feature]=content
                break
    info["recoText"]=recoText
    #print(info)
    return info

def detectIDCard(src,label=0):
    """
    检测身份证卡,要区分正方面
    label=0为正面（国徽）,反之反面
    """
    info={}
    recoText=""
    if label==0:
        rect=(60,180,320,80)
        #检测识别区
        rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,10,3,10,15,30,3,isAdaptive=True,threshVal=80)
        #分行识别,并提取关键项
        info["validity"]=""
        items=cardItem["ITEMS"]
        isSplit=False
        for img in rowImgs:
            reco=OCR.ocr(img,det=False,rec=True)
            text=reco[0][0]
            recoText+=text+";"
            if info["validity"]=="" and text!='' and reco[0][1]>0.7:
                if not isSplit:
                    index,content=getItemContent(items["validity"],text)
                    if index!=-1 and content!="":
                        info["validity"]=content
                    elif index!=-1 and content=="":
                        isSplit=True
                else:
                    info["validty"]=text
    else:
        rect1=(10,15,255,190)
        rowImgs1=imageProcess(src,rect1,cv2.THRESH_BINARY_INV,8,3,10,15,30,3)
        rect2=(10,220,400,40)
        rowImgs2=imageProcess(src,rect2,cv2.THRESH_BINARY_INV,8,3,10,15,30,3)
        #rowImgs1.extend(rowImgs2)
        #items=cardItem["ID1"]
        recos=[]
        #识别:姓名-性别-民族-出生-地址
        for img in rowImgs1:
            reco=OCR.ocr(img,det=False,rec=True)
            text=reco[0][0]
            recoText+=text+";"
            recos.append(reco)
        info=getIDFeatureInfo(cardItem["ITEMS"],cardItem["ID1"]["features"],recos)
        
        #识别:身份证号
        pattern = re.compile(r"[1-9]\d{5}(?:19|20)\d\d(?:0[1-9]|1[012])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]")
        for img in rowImgs2:
            reco=OCR.ocr(img,det=False,rec=True)
            text=reco[0][0]
            recoText+=text+";"
            if text!='' and reco[0][1]>0.7:
                result = pattern.findall(text)
                if result is not None and len(result)>0:
                    info["idNumber"]=result[0]
        #校验属性
        if info["idNumber"]!="":
            idInfo=IDFeatureCheck(info["idNumber"])
            info["gender"]=idInfo.getGender()
            info["birth"]=idInfo.getBirthday()
        else:
            info["gender"]=IDFeatureCheck.convertGender(info["gender"])
            info["birth"]=IDFeatureCheck.convertBirth(info["birth"])
    info["recoText"]=recoText
    return info           
            
def detectFZUStudentCard(src):
    """
    检测福州大学校园卡关键信息区域:先确定卡类型，再进行检测
    """
    (x,y,w,h)=detectMaxBlob(src,(10,40,100,180),100,cv2.THRESH_BINARY_INV)
    if x!=0:
        rect=(x,y,w,h)
    else:
        rect=(20,60,180,100)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,10,3,10,15,20,3)
    recoText=""
    recos=[]
    for img in rowImgs:
        reco=OCR.ocr(img,det=False,rec=True)
        text=reco[0][0]
        recoText+=text+";"
        if text!='' and reco[0][1]>0.7:
            recos.append(text)
    #循环遍历各个属性 
    info={}
    items=cardItem["ITEMS"]
    features=cardItem["FZU"]["features"] 
    for feature in features:
        info[feature]=""   

    labelIdx=0  #用来标记学号index
    pattern = re.compile(r"[a-zA-Z0-9]+")
    for idx,text in enumerate(recos):
        result = pattern.findall(text)
        if result is not None and len(result)>0:
            info["studentNumber"]=result[0]
            labelIdx=idx
    if labelIdx>0:
        for i in range(labelIdx-1,-1,-1):
            if "学号" not in recos[i]:
                info["name"]=recos[i]
                break
    if labelIdx<len(recos):
        for i in range(labelIdx+1,len(recos)):
            if "学院" in recos[i]:
                if "：" in recos[i]:
                    info["academy"]=recos[i].split("：")[-1]
                else:
                    info["academy"]=recos[i]
    info["recoText"]=recoText
    return info
    
def detectFJNUStudentCard(src):
    """
    检测福师大校园卡信息:1)卡号->姓名->性别->学院->专业；2)有效期
    """
    rect1=(140,60,240,150)
    rowImgs1=imageProcess(src,rect1,cv2.THRESH_BINARY_INV,12,3,10,15,20,3)
    #rect2=(20,240,220,40)
    #rowImgs2=imageProcess(src,rect2,cv2.THRESH_BINARY_INV,8,3,15,15,15,3)
    info=getStudentCardInfo(rowImgs1,"FJNU")
    info["gender"]=IDFeatureCheck.convertGender(info["gender"])
    info["studentNumber"]=info["cardNumber"]
    return info

def detectFJNUXHCStudentCard(src):
    """
    检测福师大校园卡信息:1)卡号->姓名->性别->专业；2)有效期
    """
    rect1=(150,60,240,150)
    rowImgs1=imageProcess(src,rect1,cv2.THRESH_BINARY_INV,12,3,10,15,18,3)
    #rect2=(20,240,220,40)
    #rowImgs2=imageProcess(src,rect2,cv2.THRESH_BINARY_INV,8,3,15,15,15,3)
    info=getStudentCardInfo(rowImgs1,"FJNUXHC")
    info["gender"]=IDFeatureCheck.convertGender(info["gender"])
    info["studentNumber"]=info["cardNumber"]
    return info

def detectMJUStudentCard(src):
    """
    闽江学院：姓名->学院->专业->学号
    """
    rect=(150,80,270,180)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,12,3,15,15,30,3)
    info=getStudentCardInfo(rowImgs,"MJU")
    return info

def detectFTUStudentCard(src):
    """
    福建工程需要:姓名->学院->学号
    """
    rect=(150,100,230,160)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,12,3,15,15,30,3)
    info=getStudentCardInfo(rowImgs,"FTU")
    return info

def detectFAAFUStudentCard(src):
    """
    福建农林大学:1）姓名->学号->学院；2）有效期
    """
    rect1=(20,70,230,160)
    rowImgs=imageProcess(src,rect1,cv2.THRESH_BINARY_INV,12,3,8,15,30,3)
    #rect2=(240,225,180,50)
    #rowImgs=imageProcess(src,rect2,cv2.THRESH_BINARY_INV,12,3,15,15,10,3)
    info=getStudentCardInfo(rowImgs,"FAAFU")
    return info

def detectFMUStudentCard(src):
    """
    福建医科大学:姓名->学号->学院
    """
    rect=(150,10,220,140)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,12,3,15,15,20,3)
    info=getStudentCardInfo(rowImgs,"FMU")
    return info

def detectFTCMUStudentCard(src):
    """
    福建中医药大学:姓名->学号->学院
    """
    rect=(160,25,220,160)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,12,3,15,15,20,3)
    return getStudentCardInfo(rowImgs,"FTCMU")

def detectMJTCStudentCard(src):
    """
    闽江师范高等专科：姓名->学号->班级
    """
    rect=(25,90,230,160)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY,12,3,8,15,30,3,isAdaptive=False,threshVal=150)
    return getStudentCardInfo(rowImgs,"MJTC")

def detectFJXCStudentCard(src):
    """
    江夏学院：姓名->性别->学号
    """
    rect=(110,60,280,110)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,12,0,10,15,20,3)
    info=getStudentCardInfo(rowImgs,"FJXC")
    info["gender"]=IDFeatureCheck.convertGender(info["gender"])
    return info

def detectFTPStudentCard(src):
    """
    职业技术学院:姓名->学号->专业
    """
    rect=(10,10,270,150)
    rowImgs=imageProcess(src,rect,cv2.THRESH_BINARY_INV,12,3,10,15,35,3,isAdaptive=False,threshVal=80)
    return getStudentCardInfo(rowImgs,"FTP")

def detectCard(src,cardType,label=0):
    """
    检测卡的接口
    """
    img=cv2.resize(src,(420,280))
    
    #cv2.imshow("src",src)
    if cardType==CARDTPYE.FZU:
        return detectFZUStudentCard(img)
    elif cardType==CARDTPYE.FJNU:
        return detectFJNUStudentCard(img)
    elif cardType==CARDTPYE.FJNUXHC:
        return detectFJNUXHCStudentCard(img)
    elif cardType==CARDTPYE.ID:
        return detectIDCard(img,label=label)
    elif cardType==CARDTPYE.MJU:
        return detectMJUStudentCard(img)
    elif cardType==CARDTPYE.FTU:
        return detectFTUStudentCard(img)
    elif cardType==CARDTPYE.FAAFU:
        return detectFAAFUStudentCard(img)
    elif cardType==CARDTPYE.FMU:
        return detectFMUStudentCard(img)
    elif cardType==CARDTPYE.FTCMU:
        return detectFTCMUStudentCard(img)
    elif cardType==CARDTPYE.MJTC:
        return detectMJTCStudentCard(img)
    elif cardType==CARDTPYE.FJXC:
        return detectFJXCStudentCard(img)
    elif cardType==CARDTPYE.FTP:
        return detectFTPStudentCard(img)
    

def main():
    image=cv2.imread(r"E:\DATASET\OCR\stu_card_cut\zyjsx0.jpg")
    detectCard(image,CARDTPYE.FTP,label=0)
    cv2.waitKey(0)


if __name__=="__main__":
    main()