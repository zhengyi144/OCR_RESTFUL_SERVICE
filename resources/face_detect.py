import face_recognition
import cv2

def detectFaceImage(image):
    faceLocs=face_recognition.face_locations(image)
    faceImgs=[]
    for faceLoc in faceLocs:
        print(faceLoc)
        top,right,bottom,left=faceLoc
        faceImg=image[right:left,top:bottom,:]
        faceImgs.append(faceImg)
    return faceImgs

def detectFace(srcPath,dstPath):
    """
    params:
       srcPath: source image path
       dstPath: result image path
    """
    image=cv2.imread(srcPath)
    faceLoctions=face_recognition.face_locations(image)
    for faceLocation in faceLoctions:
        top,right,bottom,left=faceLocation
        cv2.rectangle(image,(left,top), (right,bottom), (0,255,0), 4)
        cv2.imwrite(dstPath,image)
    
def recogniseFace(inputPath1,inputPath2):
    image01=face_recognition.load_image_file(inputPath1)
    image02=face_recognition.load_image_file(inputPath2)
    known_encoding = face_recognition.face_encodings(image01)[0]
    unknown_encoding = face_recognition.face_encodings(image02)[0]

    distance = face_recognition.face_distance([known_encoding], unknown_encoding)
    result=face_recognition.compare_faces([known_encoding], unknown_encoding)
    return distance,result[0]

