import numpy as np
import librosa
import cv2
from moviepy.editor import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import os
import subprocess
import webbrowser
from PyQt5.QtCore import *

ui=uic.loadUiType("Y:\\Kwak\\코딩\\241018_1 VideoBeatZoom\\241018_1_7.ui")[0]

class Worker(QThread):
    Bar=pyqtSignal(int)
    Finish=pyqtSignal()

    def __init__(self,wherevideo,whereaudio,whereoutput,howinlong,howoutlong,howbig,whenzoom,easein,easeout,zoomperbeat,zoomduringbeat):
        super().__init__()
        self.wherevideo=wherevideo
        self.whereaudio=whereaudio
        self.whereoutput=whereoutput
        self.howinlong=howinlong
        self.howoutlong=howoutlong
        self.howbig=howbig
        self.whenzoom=whenzoom
        self.easein=easein
        self.easeout=easeout
        self.zoomperbeat=zoomperbeat
        self.zoomduringbeat=zoomduringbeat
    
    def run(self):
        print("처리시작")
        print("EaseIn : ",self.easein)
        print("EaseOut : ",self.easeout)
        print("ZoomPerBeat : ",self.zoomperbeat)
        print("ZoomDuringBeat : ",self.zoomduringbeat)

        #오디오 추출
        y,sr=librosa.load(self.whereaudio,sr=None)

        #영상
        video_clip=VideoFileClip(self.wherevideo)
        fps=video_clip.fps
        width,height=video_clip.size
        spf=int(sr/fps)
        
        howinlongframe=int(self.howinlong*fps)
        howoutlongframe=int(self.howoutlong*fps)

        #비트레이트 추출
        video_probe=subprocess.Popen(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=bit_rate','-of','default=noprint_wrappers=1:nokey=1',self.wherevideo],
                                        stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        audio_probe=subprocess.Popen(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=bit_rate','-of','default=noprint_wrappers=1:nokey=1',self.wherevideo],
                                        stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        video_out,_=video_probe.communicate()
        audio_out,_=audio_probe.communicate()

        brv=None
        bra=None
        if video_out:
            brv=video_out.decode().strip()
        if audio_out:
            bra=audio_out.decode().strip()


        vols=[]
        for n in range(0,len(y),spf):
            audio=y[n:n+spf]
            vol=np.sqrt(np.mean(audio**2))#데시벨로 변환
            vols.append(vol)

        frames=[]
        zoom=1

        framestot=int(video_clip.duration*fps)
        #줌
        iszoom=1
        flag=0
        for framebang,frame in enumerate(video_clip.iter_frames()):
            voltemp=vols[min(len(vols)-1,framebang)]
            
            if voltemp>=self.whenzoom:
                if self.zoomperbeat==True:
                    if flag==0:
                        iszoom=0

                if self.zoomduringbeat==True:
                    iszoom=0
            else:
                flag=0

            if iszoom==0:
                if howinlongframe==0:
                    zoom=self.howbig
                else:
                    if self.easein==True:
                        zoom+=(zoom-0.9)/howinlongframe
                    elif self.easein==False:
                        zoom+=(self.howbig-1)/howinlongframe

                if zoom>=self.howbig:#줌 달성 유무
                    iszoom=1
                    flag=1

            elif iszoom==1:
                if howoutlongframe==0:
                        zoom=1
                else:
                    if self.easeout==True:
                        zoom-=(zoom-1)/howoutlongframe
                    elif self.easeout==False:
                        zoom-=(self.howbig-1)/howoutlongframe


            zoom = max(1,zoom)#작아지지 않게
            zoom = min(self.howbig, zoom)#커지지 않게

            print(zoom)

            h,w,_=frame.shape
            center_x=w//2
            center_y=h//2
            radius_x=int(w/(zoom*2))
            radius_y=int(h/(zoom*2))

            cropped=frame[max(center_y-radius_y,0):min(center_y+radius_y,h),max(center_x-radius_x,0):min(center_x+radius_x,w)]

            if zoom>1:
                zoomed=cv2.resize(cropped,(w,h))
            else:
                zoomed=frame

            frames.append(zoomed)

            self.Bar.emit(int((framebang/framestot)*100)-1)

        zoomed=ImageSequenceClip(frames,fps=fps)
        zoomed=zoomed.set_audio(video_clip.audio)

        if brv!=None and bra!=None:
            zoomed.write_videofile(self.whereoutput,codec='libx264',fps=fps,bitrate=brv,audio_bitrate=bra)
            print("영상 비트레이트 : "+str(brv))
            print("오디오 비트레이트 : "+str(bra))
        else:
            zoomed.write_videofile(self.whereoutput,codec='libx264',fps=fps)
            print("비트레이트 없다")

        self.Bar.emit(100)
        self.Finish.emit()

class WindowClass(QMainWindow,ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.ZDB.setChecked(True)
        self.EI.setChecked(True)
        self.EO.setChecked(True)

        #버튼
        self.start.clicked.connect(self.Start)
        self.github.clicked.connect(self.Github)
        self.howtouse.clicked.connect(self.Howtouse)
        self.progressBar.setValue(0)


    def Github(self):
        webbrowser.open("https://github.com/SeunggyuKwak")

    def Howtouse(self):
        webbrowser.open("https://github.com/SeunggyuKwak/VideoBeatZoom")

    def Start(self):
        #입력 검사
        if self.VL.toPlainText()==""or self.AL.toPlainText()==""or self.OL.toPlainText()==""or self.ZID.text()==""or self.ZOD.text()==""or self.AS.text()==""or self.ZR.text()=="":
            QMessageBox.warning(self,'Warning','Please enter all values')
            return
        
        wherevideo=self.VL.toPlainText()
        whereaudio=self.AL.toPlainText()
        whereoutput=self.OL.toPlainText()
        howinlong=float(self.ZID.text())
        howoutlong=float(self.ZOD.text())
        howbig=float(self.ZR.text())/100
        whenzoom=float(self.AS.text())
        easein=self.EI.isChecked()
        easeout=self.EO.isChecked()
        zoomperbeat=self.ZPB.isChecked()
        zoomduringbeat=self.ZDB.isChecked()

        #경로 검사
        if not os.path.exists(wherevideo)or not os.path.exists(whereaudio):
            QMessageBox.warning(self,'Warning','There is no such file in that path')
            return
        
        videoname=wherevideo.split("\\")
        videoname=videoname[len(videoname)-1]
        videoname=videoname.split(".")
        videoname=videoname[0]

        whereoutput=whereoutput+"\\"+videoname+"-zoomed.mp4"

        self.worker = Worker(wherevideo,whereaudio,whereoutput,howinlong,howoutlong,howbig,whenzoom,easein,easeout,zoomperbeat,zoomduringbeat)
        self.worker.Bar.connect(self.Bar)
        self.worker.Finish.connect(self.Finish)
        self.worker.start()

    def Bar(self,val):
        self.progressBar.setValue(val)
        
    def Finish(self):
        QMessageBox.information(self,'Success','Video has been saved successfully!')

if __name__=="__main__":
    app=QApplication([])
    myWindow=WindowClass()
    myWindow.show()
    app.exec_()
