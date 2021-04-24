from flask import Flask,render_template,request,jsonify
from resources.common.utils import *
from resources.common.logger import get_logger
from resources.paddle_ocr import imageOcrOperator
from resources.face_detect import detectFace,recogniseFace
from resources.process import processMain,saveCheckedInfo
from resources.auth import validsign

app = Flask(__name__)
logger=get_logger(name="app",log_file="logs/logger.log")

@app.route("/ocrdemo")
def load_ocrdemon():
    return render_template("OCRDemo.html")

@app.route("/uploadImage",methods=['POST'])
def uploadImage():
    base64Data=request.form.get('image')
    orientation=request.form.get('orientation')
    imageType=int(request.form.get("imageType"))
    if imageType==1:
        image=base64ToPilImage(base64Data,orientation,"./static/images/input.jpg")
    else:
        image=base64ToPilImage(base64Data,orientation,"./static/images/face_input.jpg")
    return "success"

@app.route("/paddleOcrOperator",methods=["GET"])
def paddleOcrOperator():
    imagePath=imageOcrOperator()
    base64Data=pilImageToBase64(imagePath)
    return jsonify({"image":base64Data.decode()})

@app.route("/faceDetectOperator",methods=["GET"])
def faceDetectOperator():
    srcPath="./static/images/input.jpg"
    dstPath="./static/images/face_result.jpg"
    detectFace(srcPath,dstPath)
    base64Data=pilImageToBase64(dstPath)
    return jsonify({"image":base64Data.decode()})

@app.route("/faceRecogniseOperator",methods=["GET"])
def faceRecogniseOperator():
    inputPath1="./static/images/input.jpg"
    inputPath2="./static/images/face_input.jpg"
    distance,result=recogniseFace(inputPath1,inputPath2)
    print(distance,result)
    return jsonify({"distance":str(distance[0]),"result":str(result)})

@app.route("/uploadAppIDImage",methods=["POST"])
@validsign(requireSign=True)
def uploadAppIDImage():
    try:
        #imageData=request.form.get('imageData')
        imageData=request.files["imageData"]
        imageOrientation=request.form.get("imageOrientation")
        userId=int(request.form.get("userId"))
        imageLabel=int(request.form.get('imageLabel')) #0表示正面，1表示反面，无正反默认0
        schoolName=request.form.get('schoolName') #学校名称
        ret=processMain(imageData,userId,0,imageOrientation=imageOrientation,imageLabel=imageLabel,schoolName=schoolName)
        if ret:
            logger.info("success uploadAppIDImage!")
            return jsonify({"code":200,"msg":"success"})
        else:
            logger.info("failed uploadAppIDImage!")
            return jsonify({"code":204,"msg":"error"})
    except Exception as e:
        logger.info("uploadAppIDImage exception:",exc_info=True)
        return jsonify({"code":204,"msg":"error"})

@app.route("/uploadFaceImage",methods=["POST"])
@validsign(requireSign=True)
def uploadFaceImage():
    #imageData=request.form.get('imageData')
    try:
        imageData=request.files["imageData"]
        userId=int(request.form.get("userId"))
        faceLandmarks=request.form.get("faceLandmarks")
        processMain(imageData,userId,1,faceLandmarks=faceLandmarks)
        logger.info("success uploadFaceImage!")
        return jsonify({"code":200,"msg":"success"})
    except Exception as e:
        logger.info("uploadFaceImage exception:",exc_info=True)
        return jsonify({"code":204,"msg":"error"})

@app.route("/uploadStudentImage",methods=["POST"])
@validsign(requireSign=True)
def uploadStudentImage():
    try:
        #imageData=request.form.get('imageData')
        imageData=request.files["imageData"]
        imageOrientation=request.form.get("imageOrientation")
        userId=int(request.form.get("userId"))
        schoolName=request.form.get('schoolName') #学校名称
        info=processMain(imageData,userId,2,imageLabel=1,schoolName=schoolName,imageOrientation=imageOrientation)
        if info is not None:
            logger.info("success uploadStudentImage!")
            return jsonify({"code":200,"msg":"success","info":info})
        else:
            logger.info("failed uploadAppIDImage!")
            return jsonify({"code":204,"msg":"error"})
    except Exception as e:
        logger.info("uploadAppIDImage exception:",exc_info=True)
        return jsonify({"code":204,"msg":"error"})

@app.route("/uploadCheckedInfo",methods=["POST"])
@validsign(requireSign=True)
def uploadCheckedInfo():
    try:
        userId=int(request.form.get("userId"))
        studentName=request.form.get("studentName")
        gender=int(request.form.get("gender"))
        birthday=request.form.get("birthday")
        schoolName=request.form.get('schoolName') #学校名称
        lng=float(request.form.get("lng"))
        lat=float(request.form.get("lat"))
        #1)存储用户校验后的数据
        saveCheckedInfo(userId,studentName,gender,birthday,schoolName,lng,lat)
        #2)返回审核结果
        logger.info("success uploadCheckedInfo!")
        return jsonify({"code":200,"msg":"success","checkResult":True})
    except Exception as e:
        logger.info("uploadCheckedInfo exception:",exc_info=True)
        return jsonify({"code":204,"msg":"error"})



if __name__ == "__main__":
    # 将host设置为0.0.0.0，则外网用户也可以访问到这个服务
    app.run(host="0.0.0.0", port=8080, debug=True)
