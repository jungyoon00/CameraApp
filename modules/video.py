from PyQt5.QtCore import *
from PyQt5.QtGui import *
from threading import Thread

from modules import colorfilters

import cv2, time, os, timeit, datetime
import mediapipe as mp
import numpy as np

gesture = {
    0:'fist', 1:'one', 2:'two', 3:'three', 4:'four', 5:'five',
    6:'six', 7:'rock', 8:'spiderman', 9:'yeah', 10:'ok', 11: 'fy',
}

target_gesture = {5:'take picture'}

KNN = None       # not trained model
my_hands = None  # empty model
mpHands = None
mpDraw = None

# knn model building
def gesture_model():
    print("Build KNN model")

    global KNN

    pretrained_file = np.genfromtxt('data/gesture_train_fy.csv', delimiter=',')
    angles = pretrained_file[:,:-1].astype(np.float32)
    labels = pretrained_file[:, -1].astype(np.float32)

    KNN = cv2.ml.KNearest_create()
    KNN.train(angles, cv2.ml.ROW_SAMPLE, labels)

# mediapipe model building
def hand_model():
    print("Build Hand model")
    max_num_hands = 1
    global mpHands, mpDraw, my_hands

    mpHands = mp.solutions.hands
    mpDraw = mp.solutions.drawing_utils
    my_hands = mpHands.Hands(
        max_num_hands=max_num_hands,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )


model_threads = [gesture_model, hand_model]
running_threads = []

for task in model_threads:
    t = Thread(target=task)
    running_threads.append(t)

for task in running_threads:
    task.start()

for task in running_threads:
    task.join()

print("========================")



class Video(QObject):

    sendImage = pyqtSignal(QImage)

    def __init__(self, widget, size:QSize):
        super().__init__()

        self.widget = widget
        self.size = size
        self.width = 600
        self.height = 450
        self.shape = None
        self.sendImage.connect(self.widget.recvImage)
        self.interval = 0.01
        self.FPS = 0
        self.hand_status = None
        self.photo_status = None
        self.take_interval = False

        self.recording = False
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.now = None
        self.record_video = None
        self.saveVideo = False

        self.sub_amount = 0
        self.add_amount = 0
        self.saturationScale = 1 # default 1

        self.lastest_path = ""

        self.colorFilterOption = None

        self.PATH = os.getcwd()
        # .jpg/jpeg or .png
        self.extension = ".png"

        SUPER_PATH = self.PATH + "\\data\\haarcascades\\"

        files = ['haarcascade_fullbody.xml',
                'haarcascade_upperbody.xml',
                'haarcascade_lowerbody.xml',
                'haarcascade_frontalface_default.xml',
                'haarcascade_eye.xml',
                ]
        
        self.filters = []
        for i in range(len(files)):
            my_filter = cv2.CascadeClassifier(SUPER_PATH+files[i])
            self.filters.append(my_filter)
        
        self.option = [0 for _ in range(len(files))]
        self.color = [QColor(255,0,0), QColor(255,128,0), QColor(255,255,0), QColor(0,255,0), QColor(0,0,255), QColor(0,0,128), QColor(128,0,128)]
    
    def setOption(self, option):
        self.option = option

    def startCam(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        except Exception as e:
            print(f"Cam Error =>{e}")
        else:
            self.bThread = True
            self.thrd = Thread(target=self.threadFunc)
            self.thrd.start()

    def stopCam(self):
        self.bThread = False
        self.FPS = 0

        try:
            self.cap.isOpened()
        except Exception as e:
            print(f"Cam is not opened. => {e}")
        else:
            self.cap.release()
    
    def setVideoObject(self):
        self.record_video = cv2.VideoWriter("./storage/videos/vid" + str(self.now) + ".avi", self.fourcc, 20.0, (self.current_window.shape[1], self.current_window.shape[0]))
   
    def getFilename(self, form:str="pic") -> str:
        now = (datetime.datetime.now()).strftime("%Y_%m_%d_%Hh%Mm%Ss")
        filename = form + str(now) + self.extension
        
        return filename
    
    def takePhoto(self, interval:int=3) -> None:
        if self.photo_status == "Once":
            self.photo_status = None
            photoname = self.getFilename()
            cv2.imwrite(f"{self.PATH}\\storage\\photos\\{photoname}", self.current_window)
        elif self.photo_status == "Once_interval":
            self.take_interval = True
            self.photo_status = None
            for i in list(range(interval))[::-1]:
                    print(i+1); time.sleep(1)
            photoname = self.getFilename()
            cv2.imwrite(self.PATH+'\\storage\\photos\\'+photoname, self.current_window)
            #time.sleep(5)
            self.take_interval = False
    
    def detect_hand(self, img):
        global mpHands, mpDraw, my_hands, KNN

        image = img.copy()
        image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = my_hands.process(image)

        if result.multi_hand_landmarks is not None:
            for res in result.multi_hand_landmarks:
                joint = np.zeros((21, 3))
                for j, lm in enumerate(res.landmark):
                    joint[j] = [lm.x, lm.y, lm.z]

                v1 = joint[[0,1,2,3,0,5,6,7,0,9,10,11,0,13,14,15,0,17,18,19],:] # Parent joint
                v2 = joint[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],:] # Child joint

                v = v2 - v1
                v = v / np.linalg.norm(v, axis=1)[:, np.newaxis]

                angles = np.arccos(np.einsum('nt,nt->n',
                    v[[0,1,2,4,5,6,8,9,10,12,13,14,16,17,18],:], 
                    v[[1,2,3,5,6,7,9,10,11,13,14,15,17,18,19],:]))
                
                angles = np.degrees(angles)

                data = np.array([angles], dtype=np.float32)
                _, results, _, _ = KNN.findNearest(data, 3)
                idx = int(results[0][0])

                output = None
                if idx in target_gesture.keys():
                    output = target_gesture[idx]

                if idx == 11:
                    try:
                        x1, y1 = tuple((joint.min(axis=0)[:2] * [img.shape[1], img.shape[0]] * 0.95).astype(int))
                        x2, y2 = tuple((joint.max(axis=0)[:2] * [img.shape[1], img.shape[0]] * 1.05).astype(int))
        
                        fy_img = img[y1:y2, x1:x2].copy()
                        fy_img = cv2.resize(fy_img, dsize=None, fx=0.05, fy=0.05, interpolation=cv2.INTER_NEAREST)
                        fy_img = cv2.resize(fy_img, dsize=(x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)
        
                        self.frame[y1:y2, x1:x2] = fy_img
                    except: pass
                
                mpDraw.draw_landmarks(self.frame, res, mpHands.HAND_CONNECTIONS)
                self.hand_status = output
                if output: self.photo_status = "Once_interval"

                if self.photo_status and not self.take_interval:
                    thread_take_photo = Thread(target=self.takePhoto)
                    thread_take_photo.start()
        else:
            thread_take_photo = Thread(target=self.takePhoto)
            thread_take_photo.start()

    def colorFilter(self, img, option):
        if option == "None": return img
        elif option == "Gray": return colorfilters.gray_filter(img)
        elif option == "Contrast": return colorfilters.contrast_filter(img)
        elif option == "Warm": return colorfilters.warm_filter(img)
        elif option == "Cool": return colorfilters.cool_filter(img)
        elif option == "Daylight": return colorfilters.daylight_filter(img)
        elif option == "Reversal": return colorfilters.reversal_filter(img)
        elif option == "Cartoon": return colorfilters.cartoon_filter(img)

        return img

    def img_Saturation(self, img, saturationScale):
        if self.colorFilterOption == "Gray": return img

        hsvImage = cv2.cvtColor(img , cv2.COLOR_BGR2HSV)
        hsvImage = np.float32(hsvImage)
        # 채널로 분리하는 함수  ( 다차원일 경우 사용)
        H, S, V = cv2.split(hsvImage)    # 분리됨
        # 유용한함수. np.clip 함수 이용하면 0보다 작으면 0으로 맞추고, 255보다 크면 255로 맞추라 할수 있다.
        S = np.clip( S * saturationScale , 0,255 ) # 계산값, 최소값, 최대값
        # 여기서는 saturation값만 조정하였다.
        # H,S,V 나눈 채널을 다시 합치는 함수
        hsvImage = cv2.merge( [ H,S,V ] )
        # 위에서 float으로 작업 했으로, 다시 uint8로 변경해야된다.
        hsvImage = np.uint8(hsvImage)
        # BGR로 다시 변경해야 , 우리가 눈으로 확인 가능 cv2라
        return cv2.cvtColor(hsvImage, cv2.COLOR_HSV2BGR)
    
    def bright(self, img):
        if self.sub_amount != 0:
            val = self.sub_amount
            if self.colorFilterOption == "Gray": return cv2.subtract(img, val)
            else: return cv2.subtract(img, np.full(img.shape, (val, val, val), dtype=np.uint8))
        elif self.add_amount != 0:
            val = self.add_amount
            if self.colorFilterOption == "Gray": return cv2.add(img, val)
            else: return cv2.add(img, np.full(img.shape, (val, val, val), dtype=np.uint8))
        else: return img

    def satur(self, img):
        if self.saturationScale != 1:
            return self.img_Saturation(img, self.saturationScale)
        return img
    
    def brightAndSatur(self, img):
        result_1 = self.bright(img)
        result_2 = self.satur(result_1)

        return result_2

    def threadFunc(self):
        while self.bThread:
            ok, frame = self.cap.read()
            self.frame = frame

            if ok:
                start_t = timeit.default_timer()

                # insert something
                thread_detect_hand = Thread(target=self.detect_hand, args=(frame,))
                thread_detect_hand.daemon = True
                thread_detect_hand.start()

                # convert part
                gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                for i in range(len(self.filters)):
                    if self.option[i]:
                        detects = self.filters[i].detectMultiScale(gray, 1.1, 5)

                        for x, y, w, h in detects:
                            r = self.color[i].red()
                            g = self.color[i].green()
                            b = self.color[i].blue()

                            cv2.rectangle(self.frame, (x,y), (x+w, y+h), (b, g, r), 2)
                
                # waiting thread.
                thread_detect_hand.join()
                
                resultImg_color = self.colorFilter(self.frame, self.colorFilterOption)
                resultImg_BS = self.brightAndSatur(resultImg_color)
                try:
                    self.current_window = resultImg_BS.copy()
                except: pass

                if self.recording:
                    self.record_video.write(resultImg_BS)
                
                if self.saveVideo:
                    self.record_video.release()
                    self.saveVideo = False

                rgb = cv2.cvtColor(resultImg_BS, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytesPerLine = ch * w
                img = QImage(rgb.data, w, h, bytesPerLine, QImage.Format_RGB888)
                resizedImg = img.scaled(self.size.width(), self.size.height(), Qt.KeepAspectRatio)

                terminate_t = timeit.default_timer()
                FPS = int(1./(terminate_t - start_t))
                self.FPS = FPS

                self.sendImage.emit(resizedImg)
            else:
                print("Cam reading Error")
            
            time.sleep(self.interval)
        
        print('thread finished.')
