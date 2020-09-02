import pytesseract
import cv2
import re
import numpy as np
from os import listdir
from os.path import isfile, join

pytesseract.pytesseract.tesseract_cmd = 'Tesseract-OCR/tesseract.exe'
path = 'data'
imgs = [f for f in listdir(path) if isfile(join(path, f))]

def cathayOCR(img, resize_num=5, threshold=128, erodeIterationTimes=3, dilateIterationTimes=1, medianBlurKernel=5, isRevert=True):
    isShowImg = False
    # resize
    img = cv2.resize(img,(img.shape[1] * int(resize_num), img.shape[0] * int(resize_num)), interpolation=cv2.INTER_CUBIC)

    # gray
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # binary
    retval, img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY_INV)

    # medianBlur
    img = cv2.medianBlur(img, medianBlurKernel)


    # 反相
    if isRevert:
        img = 255 - img

    cv2.imshow('resultImg', img)
    cv2.waitKey(0)

    return (pytesseract.image_to_string(img, lang='eng', config='--psm 7 --oem 3 -c tessedit_char_whitelist=.0123456789'))

for img_name in imgs:
    img = cv2.imread(path + '\\' + img_name)
    mask = np.zeros(img.shape, dtype=np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 10000:
            cv2.drawContours(mask, [c], -1, (255,255,255), -1)

    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    result = cv2.bitwise_and(img,img,mask=mask)
    result[mask==0] = (255,255,255)

    result = re.sub('[(){}<>]', '', cathayOCR(result))
    print(img_name + ' : ' + result)
