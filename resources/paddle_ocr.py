from paddleocr import PaddleOCR,draw_ocr
from PIL import Image

OCR=PaddleOCR()

def imageOcrOperator():
    image_path="./static/images/input.jpg"
    out_path='./static/images/orc_result.jpg'
    result = OCR.ocr(image_path)
    image = Image.open(image_path).convert('RGB')
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    im_show = draw_ocr(image, boxes, txts, scores, font_path='./static/tools/simfang.ttf')
    im_show = Image.fromarray(im_show)
    im_show.save(out_path)
    return out_path
