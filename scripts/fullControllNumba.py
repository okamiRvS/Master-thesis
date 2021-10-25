from djitellopy import tello
import keyPressModule as kp
import time
import cv2
import handTrackingModule as htm
from numba import jit
import numpy as np
import pdb

@jit(nopython=True)
def getKeyboardInput(me):
    #left-right, foward-back, up-down, yaw veloity
    lr, fb, ud, yv = 0, 0, 0, 0
    speed = 30

    if kp.getKey("LEFT"): lr = -speed
    elif kp.getKey("RIGHT"): lr = speed

    if kp.getKey("UP"): fb = speed
    elif kp.getKey("DOWN"): fb = -speed

    if kp.getKey("w"): ud = speed
    elif kp.getKey("s"): ud = -speed

    if kp.getKey("a"): yv = speed
    elif kp.getKey("d"): yv = -speed

    if kp.getKey("e"): me.takeoff(); time.sleep(3) # this allows the drone to takeoff
    if kp.getKey("q"): me.land() # this allows the drone to land

    if kp.getKey('z'):
        cv2.imwrite(f'src/tello_screenshots/{time.time()}.jpg', img)
        time.sleep(0.3)

    return [lr, fb, ud, yv]

def drawLog(img, color, checkTollerance, mean, val, state):
    scale = 2
    cv2.putText(img, f"checkTollerance: {checkTollerance}", (200,40), cv2.FONT_HERSHEY_PLAIN, scale, color, 3)
    cv2.putText(img, f"mean: {mean}", (200,100), cv2.FONT_HERSHEY_PLAIN, scale, color, 3)
    cv2.putText(img, f"val: {val}", (200,200), cv2.FONT_HERSHEY_PLAIN, scale, color, 3)
    cv2.putText(img, f"{state}", (200,300), cv2.FONT_HERSHEY_PLAIN, scale, color, 3)

def main():
    ################################################################
    ################################################################
    # THIS FILE SHOULD BE TESTED
    ################################################################
    ################################################################
    
    global img

    detector = htm.handDetector()

    BEGIN = 0
    START = 1
    TRACKING = 2

    state = BEGIN

    lenMaxQueue = 35
    queue = np.zeros(lenMaxQueue, dtype=np.int32)
    indexQueue = 0
    isQueueNotMaxLimit = True
    mean = 0
    tolleranceSTART = 2
    tolleranceTRACKING = 40

    pTime = 0
    cTime = 0

    resize = False
    getFromWebcam = True


    if getFromWebcam:
        # OPEN WEBCAM
        cv2.namedWindow("Image")
        cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        if cap.isOpened(): # try to get the first frame
            success, img = cap.read()
        else:
            success = False
    else:
        kp.init()
        me = tello.Tello()
        me.connect()
        print(me.get_battery())
        me.streamon() # to get the stream image


    while True:

        if getFromWebcam:
            success, img = cap.read()
        else:
            vals = getKeyboardInput(me)
            if not (vals[0] == vals[1] == vals[2] == vals[3] == 0):
                me.send_rc_control(vals[0], vals[1], vals[2], vals[3])
                time.sleep(0.05)

            img = me.get_frame_read().frame

        if resize:
            img = cv2.resize(img, (360, 240)) # comment to get bigger frames

        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)

        if len(lmList) != 0:
            #print(lmList[0])
            val = lmList[0][1] + lmList[0][2] # I'LL DO MEAN FOR X AND MEAN FOR Y, THIS IS JUST TRY

            # fill all the queue before start the mean
            if indexQueue < lenMaxQueue and isQueueNotMaxLimit:
                queue[indexQueue] = val
                drawLog(img, (0,0,255), 0, mean, val, "INIZIALIZATION")
                indexQueue+=1
            else:
                isQueueNotMaxLimit = False
                if indexQueue == lenMaxQueue:
                    indexQueue = 0

                queue[indexQueue] = val 
                
                if state == BEGIN:
                    mean = np.mean(queue)
                    checkStart = int(abs(mean - val))

                    if checkStart < tolleranceSTART:
                        drawLog(img, (0,255,0), checkStart, mean, val, "START")
                        state = START
                        startingPoint = (lmList[0][1], lmList[0][2])
                    else:
                        drawLog(img, (0,0,255), checkStart, mean, val, "BEGIN")
                
                if state == START:
                    # il vantaggio di mediare sugli ultimi valori è perché in questo modo se viene perso il flusso lo si può riprendere molto velocemente
                    # se si riparte dallo stesso punto in cui si è perso il tracking, diversamente bisognerà riacquisire tante nuove posizioni finchè 
                    # la nuova media non sia sotto la tolleranza
                    nlastMovements = 5
                    tmpList = []
                    if indexQueue < nlastMovements:
                        nElementFromEnd = nlastMovements - indexQueue
                        tmpList = queue[(lenMaxQueue - nElementFromEnd)::]
                        tmpList = np.concatenate((tmpList, queue[:indexQueue]))
                    else:
                        tmpList = np.array(queue[indexQueue-nlastMovements:indexQueue])
                    
                    mean = np.mean(tmpList)
                    checkStartTracking = int(abs(mean - val))
                    endingPoint = (lmList[0][1], lmList[0][2])

                    # draw the begin of the trajectory
                    cv2.circle(img, startingPoint, radius=0, color=(0,255,0), thickness=-1)

                    if checkStartTracking < tolleranceTRACKING:
                        drawLog(img, (255,0,0), checkStartTracking, mean, val, "START")
                        cv2.circle(img, endingPoint, radius=0, color=(0,255,0), thickness=-1)
                        cv2.line(img, startingPoint, endingPoint, (255,255,0), thickness=2)
                    else:
                        drawLog(img, (0,0,255), checkStartTracking, mean, val, "BEGIN")
                        state = BEGIN      

                if indexQueue < lenMaxQueue:
                    indexQueue+=1

        cTime = time.time()
        fps = 1/(cTime-pTime)
        pTime = cTime
        cv2.putText(img, f"FPS: {int(fps)}", (10,40), cv2.FONT_HERSHEY_PLAIN, 2, (255,0,255), 3) # print fps

        cv2.imshow("Image", img)
        key = cv2.waitKey(1)
        if key == 27: # exit on ESC
            break


if __name__ == "__main__":
    main()