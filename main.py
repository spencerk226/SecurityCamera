import cv2
import threading
import notifacation
import util
import datetime
import json

from util import getSettings

showImages = True
settings = util.getSettings()
cap = cv2.VideoCapture(0)
backSub = cv2.createBackgroundSubtractorKNN()
activeState = False
active = False
armed = False
recordingTime = settings["recordingTime"]
timer = None
startDelay = settings["startDelay"]
startDelayTimer = None
notifacationThread = None
out = None 

# Run once the recording timer stops, this means it is the end of the recording period.
def onTimer():
    global active
    active = False
    print("Stop doing")
    out.release()

def setTimer():
    global timer
    timer = threading.Timer( recordingTime, onTimer)

def postDelay():
    global armed 
    armed = True
    print("Armed")


def setStartDelayTimer():
    global startDelayTimer
    startDelayTimer = threading.Timer( startDelay, postDelay)

def getMotion( frame):
    global backsub
    frame = cv2.GaussianBlur(frame, (41,41), cv2.BORDER_DEFAULT)
    frame = backSub.apply(frame)
    return frame

def percentWhite( frame, motionFrame):
    numWhite = motionFrame[motionFrame > 10].size
    totalPix = motionFrame.size
    percentWhite = round( 10000 * numWhite / totalPix) / 100    
    return percentWhite

def resetTimer():
    if not timer == None:
        if timer.is_alive():
            timer.cancel()

def motionDetected():
    global active
    global timer
    global out
    
    # This only gets run initially on motion
    if not active and armed:
        print("Motion detected!")

        #alertGroup needs to be threaded so that it doesn't stop the camera
        notifacationThread = threading.Thread( target = notifacation.alertGroup, args = ("Motion detected laptop", ))
        notifacationThread.start()
        active = True
        resetTimer()
        setTimer()
        timer.start()
        timeInfo = datetime.datetime.now()
        recName = timeInfo.strftime(settings["fileNameFormat"])
        #might add check to see if file already exists, then add something so that stuff doesn't get overwritten
        out = cv2.VideoWriter(settings["videoOut"] + recName + ".mp4",cv2.VideoWriter_fourcc(*"mp4v"), 15.0, (640,480))
    else: 
        if active and armed:
            resetTimer()
            setTimer()
            timer.start()

def main():
    while 1:
        ret, frame = cap.read()
        motionFrame = getMotion( frame)
        motionDetectedBool = percentWhite( frame, motionFrame) > 4.0
    
        if motionDetectedBool:
            motionDetected()
            motionFrame = cv2.putText( motionFrame, "Motion Detected", (10,22), cv2.FONT_HERSHEY_SIMPLEX, .7, (100,100,100), 1)


        if showImages:
            cv2.imshow("Frame", frame)
            cv2.imshow("Motion", motionFrame)

        if active:
            out.write(frame)

        #exit when user presses q
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            if not timer == None:
                if timer.is_alive():
                    timer.cancel()
            break     

setStartDelayTimer()
startDelayTimer.start()
main()
