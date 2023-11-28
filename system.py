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

        lastImgBorder = QGroupBox("Lastest Image")

        self.lastView = QLabel(self)
        self.lastView.setFrameShape(QFrame.Panel)
        self.lastView.setFixedSize(12*28, 9*28)

        vbox = QVBoxLayout()
        vbox.addWidget(self.lastView)
        lastImgBorder.setLayout(vbox)

        toolField.addWidget(self.startBtn)
        toolField.addWidget(self.takephotoBtn)
        toolField.addWidget(self.storage_manageBtn)
        toolField.addWidget(self.video_settingsBtn)
        toolField.addWidget(self.recordVideoBtn)
        toolField.addWidget(lastImgBorder)

        # get video
        self.frm = QLabel(self)
        self.frm.setFrameShape(QFrame.Panel)
        self.frm.setFixedSize(120*5, 90*5)

        self.video_status = QGroupBox("Status")
        self.realtime_fps = QLabel("FPS: 0")
        self.realtime_hand_status = QLabel("HAND: None")
        self.realtime_photo_status = QLabel("PHOTO: None")
        status_align = QVBoxLayout()
        status_align.addWidget(self.realtime_fps)
        status_align.addWidget(self.realtime_hand_status)
        status_align.addWidget(self.realtime_photo_status)
        self.video_status.setLayout(status_align)

        videoField = QVBoxLayout()
        videoField.addWidget(self.frm)
        videoField.addWidget(self.video_status)

        mainField = QHBoxLayout()
        mainField.addLayout(videoField)
        mainField.addLayout(toolField)

        self.setLayout(mainField)
        self.setWindowTitle("Camera App")
        self.setFixedSize(size)
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
    
    def take_once(self):
        self.video.photo_status = "Once"
    
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
            print("de")
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

        self.gallary_area = QVBoxLayout()

        self.gallary_view = QLabel()

        self.gallary_toolbar = QHBoxLayout()
        self.gallary_back = QPushButton("<")
        self.gallary_back.clicked.connect(lambda: self.showGallary(self.GALLARY_NOWINDEX-1))

        self.gallary_go = QPushButton(">")
        self.gallary_go.clicked.connect(lambda: self.showGallary(self.GALLARY_NOWINDEX+1))

        self.gallary_index = QLabel("1")
        self.gallary_index.setAlignment(Qt.AlignCenter)

        self.gallary_toolbar.addWidget(self.gallary_back)
        self.gallary_toolbar.addWidget(self.gallary_index)
        self.gallary_toolbar.addWidget(self.gallary_go)

        self.gallary_shortcut = QHBoxLayout()
        self.gallary_slider = QSlider(Qt.Horizontal)
        self.gallary_slider.valueChanged.connect(lambda value: self.showGallary(value))

        self.allClearBtn = QPushButton("Clear")
        self.allClearBtn.clicked.connect(self.clearFiles)

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
        self.video.extension = value.lower()

    def get_settingTab(self) -> QWidget:
        tab = QWidget()
        self.colorFilters = ["None", "Gray", "Warm", "Cool", "Contrast", "Daylight", "Reversal", "Cartoon"]

        self.colorFilterSelect = QComboBox(self)
        for choice in self.colorFilters:
            self.colorFilterSelect.addItem(choice)
        
        self.colorFilterSelect.activated[str].connect(self.changeColorFilter)

        extensionFrame = QGroupBox("File Extension")

        vbox = QVBoxLayout()
        self.extensions = ["PNG", "JPG", "JPEG"]
        self.extensionSelect = QComboBox(self)
        for extension in self.extensions:
            self.extensionSelect.addItem(extension)

        self.extensionSelect.activated[str].connect(self.changeExtension)

        vbox.addWidget(self.extensionSelect)

        extensionFrame.setLayout(vbox)

        filters_field = QVBoxLayout()
        filters_field.addWidget(self.colorFilterSelect)
        filters_field.addWidget(extensionFrame)

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
        tab = QTabWidget()

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
        
        tab_setting = self.get_settingTab()
        tab_info = self.get_debugTab()

        Tabs = QTabWidget()
        Tabs.addTab(tab_setting, "Setting")
        Tabs.addTab(tab_info, "Debug")

        vbox = QVBoxLayout()
        vbox.addWidget(Tabs)

        self.settings_window.setWindowTitle("Settings")
        self.settings_window.setGeometry(300, 300, 240, 180)
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
