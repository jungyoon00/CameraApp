import cv2
import numpy as np

def gamma_function(channel, gamma):
    invGamma = 1/gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8") #creating lookup table
    channel = cv2.LUT(channel, table)
    return channel

def gray_filter(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def warm_filter(img):
    img = img.copy()

    img[:, :, 0] = gamma_function(img[:, :, 0], 0.75) # down scaling blue channel
    img[:, :, 2] = gamma_function(img[:, :, 2], 1.15) # up scaling red channel
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = gamma_function(hsv[:, :, 1], 1.2) # up scaling saturation channel
    
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def cool_filter(img):
    img = img.copy()

    img[:, :, 0] = gamma_function(img[:, :, 0], 1.25)
    img[:, :, 2] = gamma_function(img[:, :, 2], 0.85)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = gamma_function(hsv[:, :, 1], 0.8)
    
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def contrast_filter(img):
    # -----Converting image to LAB Color model-----------------------------------
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    # -----Splitting the LAB image to different channels-------------------------
    l, a, b = cv2.split(lab)
    # -----Applying CLAHE to L-channel-------------------------------------------
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    # -----Merge the CLAHE enhanced L-channel with the a and b channel-----------
    limg = cv2.merge((cl, a, b))
    # -----Converting image from LAB Color model to RGB model--------------------
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def daylight_filter(img):
    DAYLIGHT = 1.15

    image_HLS = cv2.cvtColor(img,cv2.COLOR_BGR2HLS) # Conversion to HLS
    image_HLS = np.array(image_HLS, dtype = np.float64)
    image_HLS[:,:,1] = image_HLS[:,:,1]*DAYLIGHT # scale pixel values up for channel 1(Lightness)
    image_HLS[:,:,1][image_HLS[:,:,1]>255]  = 255 # Sets all values above 255 to 255
    image_HLS = np.array(image_HLS, dtype = np.uint8)
    
    return cv2.cvtColor(image_HLS,cv2.COLOR_HLS2BGR) # Conversion to RGB

def reversal_filter(img):
    return cv2.bitwise_not(img)

def cartoon_filter(img):
    h, w = img.shape[:2]
    img2 = cv2.resize(img, (w//2, h//2))

    blr = cv2.bilateralFilter(img2, -1, 20, 7)
    edge = 255 - cv2.Canny(img2, 80, 120)
    edge = cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
    dst = cv2.bitwise_and(blr, edge) # and연산
    dst = cv2.resize(dst, (w, h), interpolation=cv2.INTER_NEAREST)
                                                                  
    return dst