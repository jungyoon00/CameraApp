from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from threading import Thread

from modules import video as vd

import time, sys, glob, os, datetime

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        size = QSize(1000, 600)

        self.update = True
        self.interval = 0.01

        self.helpIndex = 0
        self.helpList = ["'start cam' 버튼을 누르면\n여러 쓰레드를 한꺼번에 실행하기 때문에\n로딩에 꽤 오랜 시간이 걸립니다.\n다시 한번 누르면 카메라가 꺼집니다.",
                         "'take picture' 버튼을 누르면\n현재 보이는 화면의 사진이 찍히고\nstorage의 photos에 저장됩니다.",
                         "'open gallary' 버튼을 눌러서\n현재 photos에 있는 사진들을 갤러리처럼\n확인할 수 있습니다.",
                         "'setting'를 누르면 2가지 탭이 있습니다.\n================================\n첫번째 탭인 'Setting'은 화면과 관련된\n요소들을 조정할 수 있게 해줍니다.\n\n\n[1]",
                         "왼쪽 위에 있는 드롭다운은 필터를 적용합니다.\n그 아래의 드롭다운은 사진 촬영 시 저장할\n파일의 확장자를 지정합니다.\n\n\n[2]",
                         "오른쪽에 있는 슬라이드들은 오른쪽부터\n채도와 밝기를 조절할 수 있습니다.\n\n\n[3]",
                         "'setting'를 누르면 2가지 탭이 있습니다.\n================================\n두번째 탭인 'Debug'는 얼굴을 포함한\n여러 신체부위를 인식하는 기능을 가집니다.\n이는 사용자를 위한 기능이 아닙니다.",
                         "'start recording' 버튼을 누르면\n녹화가 시작되고 다시 한번 누르면\n녹화가 종료됨과 동시에 storage의 videos에\n저장됩니다.",]

        self.initUI(size)
        self.video = vd.Video(self, QSize(self.frm.width(), self.frm.height()))

    def initUI(self, size):
        toolField = QVBoxLayout()

        self.startBtn = QPushButton('start cam', self)
        self.startBtn.setCheckable(True)
        self.startBtn.clicked.connect(self.onoffCam)
        self.takephotoBtn = QPushButton('take picture', self)
        self.takephotoBtn.clicked.connect(self.take_once)
        self.recordVideoBtn = QPushButton('start recording', self)
        self.recordVideoBtn.setCheckable(True)
        self.recordVideoBtn.clicked.connect(self.onoffRecord)
        self.storage_manageBtn = QPushButton('open gallary', self)
        self.storage_manageBtn.clicked.connect(self.openStorage)
        self.video_settingsBtn = QPushButton('settings', self)
        self.video_settingsBtn.clicked.connect(self.openSettings)

        buttons = [self.startBtn, self.takephotoBtn, self.recordVideoBtn, self.storage_manageBtn, self.video_settingsBtn]
        for button in buttons:
            button.setStyleSheet("border-radius: 2px;"
                                 "border: 2px solid #E0E1DD;"
                                 "background: none;"
                                 "font-family: Arial;"
                                 "color: #E0E1DD;"
                                 "font-weight: 400%;")
            button.setMaximumHeight(30)

        HelpBorder = QGroupBox("HELP")
        HelpBorder.setStyleSheet("border: 2px solid #E0E1DD;"
                         "border-radius: 3px;"
                         "font-size: 15px;"
                         "color: #E0E1DD;")

        self.helpView = QLabel(self)
        self.helpView.setAlignment(Qt.AlignCenter)
        self.helpView.setFrameShape(QFrame.Panel)
        self.helpView.setFixedSize(12*28, 9*28)

        self.helpView.setStyleSheet("border: none;"
                                    "font: Arial;"
                                    "font-size: 13px;"
                                    "font-weight: 300%;"
                                    "border-radius: 3px;"
                                    "background-color: #E0E1DD;"
                                    "color: black;")

        self.beforeHelpBtn = QPushButton("<")
        self.beforeHelpBtn.clicked.connect(self.beforeHelpIndex)
        self.beforeHelpBtn.setMaximumSize(120, 50)
        self.beforeHelpBtn.setStyleSheet("color: #E0E1DD;"
                                         "font: Arial;"
                                         "font-size: 20px;"
                                         "border: none;")
        self.afterHelpBtn = QPushButton(">")
        self.afterHelpBtn.clicked.connect(self.afterHelpIndex)
        self.afterHelpBtn.setMaximumSize(120, 50)
        self.afterHelpBtn.setStyleSheet("color: #E0E1DD;"
                                        "font: Arial;"
                                        "font-size: 20px;"
                                        "border: none;")

        hbox = QHBoxLayout()
        hbox.addWidget(self.beforeHelpBtn)
        hbox.addWidget(self.afterHelpBtn)

        vbox = QVBoxLayout()
        vbox.addWidget(self.helpView)
        vbox.addLayout(hbox)
        HelpBorder.setLayout(vbox)

        toolField.addWidget(self.startBtn)
        toolField.addWidget(self.takephotoBtn)
        toolField.addWidget(self.storage_manageBtn)
        toolField.addWidget(self.video_settingsBtn)
        toolField.addWidget(self.recordVideoBtn)
        toolField.addWidget(HelpBorder)

        # get video
        self.frm = QLabel(self)
        self.frm.setFrameShape(QFrame.Panel)
        self.frm.setFixedSize(120*5, 90*5)

        self.frm.setStyleSheet("background-color: #E0E1DD;"
                               "border: none;"
                               "border-radius: 3px;")

        self.video_status = QGroupBox("Status")
        self.realtime_fps = QLabel("FPS: 0")
        self.realtime_hand_status = QLabel("HAND: None")
        self.realtime_photo_status = QLabel("PHOTO: None")
        status_align = QVBoxLayout()
        status_align.addWidget(self.realtime_fps)
        status_align.addWidget(self.realtime_hand_status)
        status_align.addWidget(self.realtime_photo_status)
        self.video_status.setLayout(status_align)

        self.video_status.setStyleSheet("background-color: #E0E1DD;"
                                        "border: none;"
                                        "border-radius: 3px;")

        videoField = QVBoxLayout()
        videoField.addWidget(self.frm)
        videoField.addWidget(self.video_status)

        mainField = QHBoxLayout()
        mainField.addLayout(videoField)
        mainField.addLayout(toolField)

        self.setHelp()

        self.setLayout(mainField)
        self.setWindowTitle("Camera App")
        self.setFixedSize(size)

        self.setAutoFillBackground(True)
        mainPal = QPalette()
        mainPal.setColor(QPalette.Background, QColor("#0D1B2A"))
        self.setPalette(mainPal)
        self.setWindowIcon(QIcon("./data/icons/camera.png"))

        self.show()

    def onoffCam(self, e):
        if self.startBtn.isChecked():
            print("Loading...")
            self.update = True
            self.thrd = Thread(target=self.statusEvent)
            self.thrd.start()

            self.startBtn.setText("stop cam")
            self.video.startCam()
            
        else:
            self.update = False
            
            self.startBtn.setText("start cam")
            self.video.stopCam()

            self.last_updating = False

    def onoffRecord(self, e):
        if self.recordVideoBtn.isChecked():
            self.video.now = (datetime.datetime.now()).strftime("%Y_%m_%d_%Hh%Mm%Ss")
            self.video.setVideoObject()
            self.video.recording = True
            self.recordVideoBtn.setText("stop recording")
            
        else:
            self.recordVideoBtn.setText("start recording")
            self.video.recording = False
            self.video.saveVideo = True
            self.video.now = None
    
    def setHelp(self):
        self.helpView.setText(self.helpList[self.helpIndex])
    
    def beforeHelpIndex(self):
        self.helpIndex -= 1
        if self.helpIndex < 0:
            self.helpIndex = len(self.helpList)-1
        
        self.setHelp()

    def afterHelpIndex(self):
        self.helpIndex += 1
        if self.helpIndex >= len(self.helpList):
            self.helpIndex = 0
        
        self.setHelp()
    
    def take_once(self):
        self.video.photo_status = "Once"
        if not self.video.bThread:
            self.popup("Alert", "Please open camera.")
        else:
            self.popup("Alert", "Picture saved.")
    
    def popup(self, title, message):
        self.popup_window = QDialog()

        self.popup_window.setWindowTitle("Alert")
        self.popup_window.setGeometry(850, 500, 200, 100)

        vbox = QVBoxLayout()
        message_label = QLabel(str(message), self)
        message_label.setStyleSheet("color: #E0E1DD;"
                                    "font-family: Arial;"
                                    "font-weight: 400%;"
                                    "font-size: 13px;")
        outBtn = QPushButton("Okay")
        outBtn.clicked.connect(lambda: self.popup_window.destroy())
        outBtn.setStyleSheet("border-radius: 2px;"
                             "border: none;"
                             "color: black;"
                             "background-color: #E0E1DD;")
        outBtn.setMaximumHeight(25)
        vbox.addWidget(message_label)
        vbox.addWidget(outBtn)

        self.popup_window.setLayout(vbox)
        self.popup_window.setAutoFillBackground(True)

        popupPal = QPalette()
        popupPal.setColor(QPalette.Background, QColor("#0D1B2A"))
        self.popup_window.setPalette(popupPal)
        self.popup_window.setWindowIcon(QIcon("./data/icons/info.png"))

        self.popup_window.show()
    
    def getPathes(self):
        photo_path = self.video.PATH + "\\storage\\photos\\"
        pathes = glob.glob(photo_path+"*")

        return pathes
    
    def showGallary(self, index):
        self.GALLARY_NOWINDEX = index

        pathes = self.getPathes()

        if not pathes:
            print("No pictures.")
            return

        try:
            picture_path = pathes[index]
        except: return

        PICTURE = QPixmap(picture_path)

        self.gallary_view.setPixmap(PICTURE)

        self.gallary_toolbar_check(len(pathes))
        self.gallary_slider.setRange(0, len(pathes)-1)
        self.gallary_index.setText(str(index+1))
    
    def gallary_toolbar_check(self, path_length) -> None:
        if self.GALLARY_NOWINDEX == 0:
            self.gallary_back.setDisabled(True)
            self.gallary_go.setEnabled(True)
        elif path_length == 1:
            self.gallary_back.setEnabled(True)
            self.gallary_go.setEnabled(True)
        elif self.GALLARY_NOWINDEX == path_length-1:
            self.gallary_go.setDisabled(True)
            self.gallary_back.setEnabled(True)
        else:
            self.gallary_back.setEnabled(True)
            self.gallary_go.setEnabled(True)
    
    def clearFiles(self) -> None:
        pathes = self.getPathes()
        [os.remove(path) for path in pathes]
        self.gallary_back.setDisabled(True)
        self.gallary_go.setDisabled(True)
    
    # graphics view.
    def createStorageWindow(self):
        self.GALLARY_NOWINDEX = 0

        self.storage_window = QDialog(self)
        self.storage_window.setWindowIcon(QIcon("./data/icons/storage.png"))
        self.setAutoFillBackground(True)
        storagePal = QPalette()
        storagePal.setColor(QPalette.Background, QColor("#0D1B2A"))
        self.storage_window.setPalette(storagePal)

        self.gallary_area = QVBoxLayout()

        self.gallary_view = QLabel()

        self.gallary_toolbar = QHBoxLayout()
        self.gallary_back = QPushButton("<")
        self.gallary_back.clicked.connect(lambda: self.showGallary(self.GALLARY_NOWINDEX-1))
        self.gallary_back.setStyleSheet("border-radius: 2px;"
                                        "border: 1px solid #E0E1DD;"
                                        "background: none;"
                                        "font-family: Arial;"
                                        "color: #E0E1DD;"
                                        "font-weight: 400%;")
        self.gallary_back.setMaximumSize(120, 50)

        self.gallary_go = QPushButton(">")
        self.gallary_go.clicked.connect(lambda: self.showGallary(self.GALLARY_NOWINDEX+1))
        self.gallary_go.setStyleSheet("border-radius: 2px;"
                                      "border: 1px solid #E0E1DD;"
                                      "background: none;"
                                      "font-family: Arial;"
                                      "color: #E0E1DD;"
                                      "font-weight: 400%;")
        self.gallary_go.setMaximumSize(120, 50)

        self.gallary_index = QLabel("1")
        self.gallary_index.setAlignment(Qt.AlignCenter)
        self.gallary_index.setStyleSheet("color: #E0E1DD;"
                                         "font-weight: 400%;")

        self.gallary_toolbar.addWidget(self.gallary_back)
        self.gallary_toolbar.addWidget(self.gallary_index)
        self.gallary_toolbar.addWidget(self.gallary_go)

        self.gallary_shortcut = QHBoxLayout()
        self.gallary_slider = QSlider(Qt.Horizontal)
        self.gallary_slider.valueChanged.connect(lambda value: self.showGallary(value))

        self.allClearBtn = QPushButton("Clear")
        self.allClearBtn.clicked.connect(self.clearFiles)
        self.allClearBtn.setStyleSheet("border-radius: 2px;"
                                       "border: 1px solid #E0E1DD;"
                                       "background: none;"
                                       "font-family: Arial;"
                                       "color: #E0E1DD;"
                                       "font-weight: 400%;")
        self.allClearBtn.setMaximumSize(120, 50)

        self.gallary_shortcut.addWidget(self.gallary_slider)
        self.gallary_shortcut.addWidget(self.allClearBtn)

        self.gallary_area.addWidget(self.gallary_view)
        self.gallary_area.addLayout(self.gallary_toolbar)
        self.gallary_area.addLayout(self.gallary_shortcut)

        self.storage_window.setWindowTitle("Storage")
        self.storage_window.setWindowModality(Qt.NonModal)

        self.showGallary(self.GALLARY_NOWINDEX)

        self.storage_window.setLayout(self.gallary_area)
        self.storage_window.show()
    
    def openStorage(self):
        self.createStorageWindow()

    def changeColorFilter(self, value:str):
        self.video.colorFilterOption = value

    def brightnessChange(self, value:int) -> None:
        if value == 50:
            self.video.add_amount = 0
            self.video.sub_amount = 0
        elif value < 50:
            self.video.add_amount = 0
            self.video.sub_amount = (50 - value)*2
        elif value > 50:
            self.video.add_amount = (value - 50)*2
            self.video.sub_amount = 0

    def saturationChange(self, value:int):
        if value == 50:
            self.video.saturationScale = 1
        elif value < 50:
            self.video.saturationScale = ((value + 1)*2 - 1)/100
        elif value > 50:
            self.video.saturationScale = 1 + ((value - 50)*2 - 1)/100
    
    def changeExtension(self, value:str):
        self.video.extension = "." + value.lower()

    def resetValues(self):
        self.video.colorFilterOption = "None"
        self.colorFilterSelect.setCurrentIndex(0)

        self.video.extension = "PNG"
        self.extensionSelect.setCurrentIndex(0)

        self.video.saturationScale = 1
        self.saturationSlide.setValue(50)

        self.video.add_amount = 0
        self.video.sub_amount = 0
        self.brightnessSlide.setValue(50)

    def get_settingTab(self) -> QWidget:
        tab = QWidget()
        self.colorFilters = ["None", "Gray", "Warm", "Cool", "Contrast", "Daylight", "Reversal", "Cartoon"]

        tab.setAutoFillBackground(True)
        settingPal = QPalette()
        settingPal.setColor(QPalette.Background, QColor("#1B263B"))
        tab.setPalette(settingPal)

        tab.setStyleSheet("font-family: Arial;"
                          "font-size: 13px;"
                          "font-weight: 400%;"
                          "color: #E0E1DD")

        self.colorFilterSelect = QComboBox(self)
        for choice in self.colorFilters:
            self.colorFilterSelect.addItem(choice)
        
        self.colorFilterSelect.activated[str].connect(self.changeColorFilter)

        self.colorFilterSelect.setStyleSheet("color: black;"
                                             "font-family: Arial;"
                                             "border: none;"
                                             "border-radius: 2px;"
                                             "background-color: white;")

        extensionFrame = QGroupBox("File Extension")

        vbox = QVBoxLayout()
        self.extensions = ["PNG", "JPG", "JPEG"]
        self.extensionSelect = QComboBox(self)
        for extension in self.extensions:
            self.extensionSelect.addItem(extension)
        
        self.extensionSelect.setStyleSheet("color: balck;"
                                           "font-family: Arial;"
                                           "border: none;"
                                           "border-radius: 2px;"
                                           "background-color: white;")

        self.extensionSelect.activated[str].connect(self.changeExtension)

        vbox.addWidget(self.extensionSelect)

        extensionFrame.setLayout(vbox)

        self.resetBtn = QPushButton("Reset", self)
        self.resetBtn.clicked.connect(self.resetValues)

        self.resetBtn.setStyleSheet("border: none;"
                                    "border-radius: 2px;"
                                    "background-color: white;"
                                    "font-family: Arial;"
                                    "color: black;")
        
        self.resetBtn.setMaximumHeight(25)

        filters_field = QVBoxLayout()
        filters_field.addWidget(self.colorFilterSelect)
        filters_field.addWidget(extensionFrame)
        filters_field.addWidget(self.resetBtn)

        brightGroup = QGroupBox("Bright")

        self.brightnessSlide = QSlider()
        self.brightnessSlide.setRange(0, 100)
        self.brightnessSlide.setValue(50) # standard 50
        self.brightnessSlide.valueChanged.connect(self.brightnessChange)
        
        bright_vbox = QVBoxLayout()
        bright_vbox.addWidget(self.brightnessSlide)
        brightGroup.setLayout(bright_vbox)

        saturGroup = QGroupBox("Satur")

        self.saturationSlide =QSlider()
        self.saturationSlide.setRange(0, 100)
        self.saturationSlide.setValue(50) # standard 50
        self.saturationSlide.valueChanged.connect(self.saturationChange)

        satur_vbox = QVBoxLayout()
        satur_vbox.addWidget(self.saturationSlide)
        saturGroup.setLayout(satur_vbox)

        sliders_field = QHBoxLayout()
        sliders_field.addWidget(brightGroup)
        sliders_field.addWidget(saturGroup)

        tab_field = QHBoxLayout()
        tab_field.addLayout(filters_field)
        tab_field.addLayout(sliders_field)

        tab.setLayout(tab_field)

        return tab

    def get_debugTab(self) -> QWidget:
        tab = QWidget()
        tab.setAutoFillBackground(True)

        debugPal = QPalette()
        debugPal.setColor(QPalette.Background, QColor("#1B263B"))
        tab.setPalette(debugPal)

        tab.setStyleSheet("font-family: Arial;"
                          "font-size: 13px;"
                          "font-weight: 400%;"
                          "color: #E0E1DD")

        self.faceOption = QCheckBox("Face")
        self.faceOption.clicked.connect(self.getOption)
        self.eyeOption = QCheckBox("Eye")
        self.eyeOption.clicked.connect(self.getOption)
        self.fullBodyOption = QCheckBox("Full Body")
        self.fullBodyOption.clicked.connect(self.getOption)
        self.upperBodyOption = QCheckBox("Upper Body")
        self.upperBodyOption.clicked.connect(self.getOption)
        self.lowerBodyOption = QCheckBox("Lower Body")
        self.lowerBodyOption.clicked.connect(self.getOption)
        self.glassesOption = QCheckBox("Glasses")
        self.glassesOption.clicked.connect(self.getOption)

        option_box = QGroupBox("<Dev Option>")
        option_field = QVBoxLayout()
        option_field.addWidget(self.faceOption)
        option_field.addWidget(self.eyeOption)
        option_field.addWidget(self.fullBodyOption)
        option_field.addWidget(self.upperBodyOption)
        option_field.addWidget(self.lowerBodyOption)
        option_field.addWidget(self.glassesOption)

        option_box.setLayout(option_field)

        vbox = QVBoxLayout()
        vbox.addWidget(option_box)

        tab.setLayout(vbox)

        return tab

    def createSettingsWindow(self):
        self.settings_window = QDialog(self)
        self.settings_window.setAutoFillBackground(True)
        
        settingPal = QPalette()
        settingPal.setColor(QPalette.Background, QColor("#0D1B2A"))
        self.settings_window.setPalette(settingPal)
        self.settings_window.setWindowIcon(QIcon("./data/icons/setting.png"))
        
        tab_setting = self.get_settingTab()
        tab_info = self.get_debugTab()

        Tabs = QTabWidget()
        Tabs.addTab(tab_setting, "Setting")
        Tabs.addTab(tab_info, "Debug")

        vbox = QVBoxLayout()
        vbox.addWidget(Tabs)

        self.settings_window.setWindowTitle("Settings")
        self.settings_window.setGeometry(850, 300, 240, 180)
        self.settings_window.setWindowModality(Qt.NonModal)
        self.settings_window.setLayout(vbox)

        self.settings_window.show()
    
    def openSettings(self):
        self.createSettingsWindow()
    
    def getOption(self):
        options = [ False for _ in range(6) ]
    
        if self.faceOption.isChecked(): options[3] = True
        elif self.eyeOption.isChecked(): options[4] = True
        elif self.fullBodyOption.isChecked(): options[0] = True
        elif self.upperBodyOption.isChecked(): options[1] = True
        elif self.lowerBodyOption.isChecked(): options[2] = True
        elif self.glassesOption.isChecked(): options[5] = True
    
        self.video.setOption(options)
    
    def recvImage(self, img):
        self.frm.setPixmap(QPixmap.fromImage(img))
    
    def closeEvent(self, e):
        self.video.stopCam()
    
    def statusEvent(self):
        while self.update:
            self.realtime_fps.setText(f"FPS: {self.video.FPS}")
            self.realtime_hand_status.setText(f"HAND: {self.video.hand_status}")
            self.realtime_photo_status.setText(f"PHOTO: {self.video.photo_status}")

            time.sleep(self.interval)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
