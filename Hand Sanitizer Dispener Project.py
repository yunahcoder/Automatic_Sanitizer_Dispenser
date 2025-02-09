import cv2
import mediapipe as mp
import math
import serial
import numpy as np
from picamera2 import Picamera2
import RPi.GPIO as GP
from time import sleep
import ADC
GP.setmode(GP.BOARD)
ADC.setup()

class mpHands:
    import mediapipe as mp
    def __init__(self,maxHands=2):
        self.hands=self.mp.solutions.hands.Hands(False,maxHands)
    def Marks(self,frame):
        myHands=[]
        frameRGB=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        results=self.hands.process(frameRGB)
        if results.multi_hand_landmarks != None:
            for handLandMarks in results.multi_hand_landmarks:
                myHand=[]
                for landMark in handLandMarks.landmark:
                    myHand.append((int(landMark.x*width),int(landMark.y*height)))
                myHands.append(myHand)
        return myHands

def Dispense(size):
    sleep(1)

    distime=size
    GP.output(GreenLED,True)
    MP.ChangeDutyCycle(50)
    GP.output(Men1,True)
    GP.output(Men2,False)   
    sleep(distime)
    GP.output(Men1,False)
    GP.output(Men2,False)
    sleep(0.3)
    LocSW=1
    while LocSW==1:
        LocSW=GP.input(MlocSW)
        MP.ChangeDutyCycle(15)
        GP.output(Men1,False)
        GP.output(Men2,True)

    GP.output(GreenLED,False)
    GP.output(Men1,False)
    GP.output(Men2,False)
    print("Time revolved: ",distime)
    sleep(1)
    return True


picam=Picamera2()
width=608
height=1024
picam.preview_configuration.main.size=(width,height)
picam.preview_configuration.main.format="RGB888"
picam.preview_configuration.controls.FrameRate=30
picam.preview_configuration.align()
picam.configure("preview")
picam.start()

findHands=mpHands(1)
Mspeed=36
Men1=38
Men2=40
MlocSW=19
DoorSW=21
GreenLED=23

GP.setup(MlocSW,GP.IN,pull_up_down=GP.PUD_UP)
GP.setup(DoorSW,GP.IN,pull_up_down=GP.PUD_UP)
GP.setup(GreenLED,GP.OUT)
GP.setup(Men1,GP.OUT)
GP.setup(Men2,GP.OUT)
GP.setup(Mspeed,GP.OUT)
MP=GP.PWM(Mspeed,100)
MP.start(60)
cm_area=0
total_area=0
dispensed_amount=0
DisResult=False
cv2.namedWindow("Hand Sanitizer Dispenser", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Hand Sanitizer Dispenser",cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
    if DisResult==True:
        sleep(2)
        DisResult=False

    frame0=picam.capture_array()
    frame=cv2.flip(frame0,-1)
    handData=findHands.Marks(frame)
    Mloc=GP.input(MlocSW)
    Door=GP.input(DoorSW)
    if Mloc==0:
        GP.output(Men1,False)
        GP.output(Men2,False)
        
    for hand in handData:
        for ind in [0,1,5,17]:
            cv2.circle(frame,hand[ind],10,(255,0,0),-1)
        for ind in [2,3,4,6,7,8,9,10,11,12,13,14,15,16,18,19,20]:
            cv2.circle(frame,hand[ind],5,(0,0,255),-1)
            cv2.line(frame,(hand[0][0],hand[0][1]),(hand[17][0],hand[17][1]),(255,0,0),3)
            cv2.line(frame,(hand[0][0],hand[0][1]),(hand[1][0],hand[1][1]),(255,0,0),3)
            cv2.line(frame,(hand[1][0],hand[1][1]),(hand[5][0],hand[5][1]),(255,0,0),3)
            cv2.line(frame,(hand[17][0],hand[17][1]),(hand[5][0],hand[5][1]),(255,0,0),3)
            a1=int(math.sqrt((hand[1][0]-hand[0][0])**2 + (hand[1][1]-hand[0][1])**2))
            b1=int(math.sqrt((hand[1][0]-hand[5][0])**2 + (hand[1][1]-hand[5][1])**2))
            c1=int(math.sqrt((hand[0][0]-hand[5][0])**2 + (hand[0][1]-hand[5][1])**2))
            a2=int(math.sqrt((hand[5][0]-hand[17][0])**2 + (hand[5][1]-hand[17][1])**2))
            b2=int(math.sqrt((hand[0][0]-hand[17][0])**2 + (hand[0][1]-hand[17][1])**2))
            c2=int(math.sqrt((hand[0][0]-hand[5][0])**2 + (hand[0][1]-hand[5][1])**2))
            s1=int((a1+b1+c1)/2)
            s2=int((a2+b2+c2)/2)
            if s1*(s1-a1)*(s1-b1)*(s1-c1) < 0 or s2*(s2-a2)*(s2-b2)*(s2-c2) < 0: 
                print("N/A")
            else:  
                area1=math.sqrt(s1*(s1-a1)*(s1-b1)*(s1-c1))
                area2=math.sqrt(s2*(s2-a2)*(s2-b2)*(s2-c2))
                total_area=int(area1+area2)
                cv2.putText(frame,"Palm Size In Pixels: " + str(total_area),(10,980),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)

    analogVal=ADC.getResult(0)
#    print(analogVal)
    #cv2.putText(frame,"Distance From Sensor: " + str(analogVal),(10,930),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)
    if 27< analogVal < 40:
        cv2.putText(frame,"Raise Your Hand A Little, Please",(20,500),cv2.FONT_HERSHEY_TRIPLEX,1,(0,0,255),2) 
    if analogVal > 50:
        cv2.putText(frame,"Lower Your Hand A Little, Please",(20,500),cv2.FONT_HERSHEY_TRIPLEX,1,(0,0,255),2) 
    if total_area > 25000 and 40<analogVal<50 and Door==1:
        calculatedtime = round(float(((0.5/70000)*total_area)-0.0145),2)
        if total_area <= 30000:
            calculatedtime=0.2
        if total_area >= 100000:
            calculatedtime=0.7
        dispensed_amount = round(((1.1/0.5)*calculatedtime)-0.34,2)
        DisResult=Dispense(calculatedtime)
        print("Amount Dispensed:" + str(dispensed_amount)+"ml")
        print("Palm Area: " + str(total_area))

    if DisResult==True:
        cv2.putText(frame,("Amount Dispensed: " + str(dispensed_amount) +"ml"),(50,500),cv2.FONT_HERSHEY_TRIPLEX,1,(0,255,0),2) 
        cv2.putText(frame,"Have a Nice Day! :)",(50,600),cv2.FONT_HERSHEY_TRIPLEX,1,(0,255,0),2)
        cv2.imshow('Hand Sanitizer Dispenser', frame)
        sleep(1)
    if DisResult==False:
        cv2.imshow('Hand Sanitizer Dispenser', frame)
        
    if cv2.waitKey(1)==ord('q'):
        break
cv2.destroyAllWindows()
GP.cleanup()