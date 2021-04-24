import base64
import cv2
from PIL import Image
import numpy as np
from io import BytesIO
import re

def imageFromBase64(base64Str):
    base64Data = re.sub('^data:image/.+;base64,', '', base64Str)
    decodeData=base64.b64decode(base64Data)
    return decodeData

def imageFileToCvImage(imageFile):
    image=Image.open(imageFile)
    return pImageToCvImage(image)

def pImageToCvImage(pImage):
    return cv2.cvtColor(np.asarray(pImage),cv2.COLOR_RGB2BGR)

def base64ToCvImage(base64Data,orientation):
    image=base64ToPilImage(base64Data,orientation)
    image=pImageToCvImage(image)
    return image

def base64ToPilImage(base64Data,orientation,imagePath=None):
    """
    orientation:1,3,6,8分别代表0,180，顺时90，逆时90
    """
    decodeData=imageFromBase64(base64Data)
    image=BytesIO(decodeData)
    image=Image.open(image)
    if orientation!=None and orientation!="":
        orientation=int(orientation)
    if orientation==3:
        image=image.transpose(Image.ROTATE_180)
    elif orientation==6:
        image=image.transpose(Image.ROTATE_270)
    elif orientation==8:
        image=image.transpose(Image.ROTATE_90)
    if imagePath:
        image.save(imagePath)
    return image

def pilImageToBase64(imagePath):
    image=Image.open(imagePath)
    outBuffer=BytesIO()
    image.save(outBuffer,format="JPEG")
    base64Data=base64.b64encode(outBuffer.getvalue())
    return base64Data