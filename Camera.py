import os
import sys

import cv2
import face_recognition

from DynamicAddition import pauseCamera
from TransferLearning import loadDictionary, loadLists, toList, getLivenessValue, runInParallel, dynamicAdd, \
    getFolderSize, checkIfHere
from init import *
import numpy as np
from Excel import *
from LivenessDetection import getModel, getModelPred

ds_factor = 0.6
face_cascade = cv2.CascadeClassifier("Cascades/data/haarcascade_frontalface_alt2.xml")

global dynamicState
global pauseState
dynamicState = False
pauseState = True


def addPerson():
    global dynamicState
    dynamicState = True


class VideoCamera(object):
    def __init__(self, source):
        try:
            self.video = cv2.VideoCapture(source)
            global processThisFrame, faceLocations, faceEncodings, faceNames, encodingList, encodingNames
            global faceNamesKnown, fullStudentNames, inputFrames, model

            # Initialize some variables
            faceLocations = []
            faceEncodings = []
            faceNames = []
            inputFrames = []
            processThisFrame = True

            fullStudentNames = loadLists("List Information/Full Student Names")  # List with full Student Names
            faceNamesKnown = loadLists("List Information/Face Names Known")  # List With Face Names
            encodingNames = loadLists("List Information/Encoding Names")  # List With encoding names
            loadDictionary("List Information/Face Names Known", faceEncodingsKnown)  # Dictionary with Encodings
            encodingList = toList(faceEncodingsKnown)
            for x in range(0, int(len(encodingList))):
                encodingList[x] = np.load("Encodings/" + str(encodingNames[x]))

            # model = getModelPred()

        except Exception as e:
            print(e)

    def __del__(self):
        self.video.release()

    def additionProcess(self):
        global encodingList, encodingNames, faceEncodingsKnown
        global faceNamesKnown, fullStudentNames

        fullStudentNames = loadLists(
            "List Information/Full Student Names")  # List with full Student Names
        faceNamesKnown = loadLists("List Information/Face Names Known")  # List With Face Names
        encodingNames = loadLists("List Information/Encoding Names")  # List With encoding names
        loadDictionary("List Information/Face Names Known",
                       faceEncodingsKnown)  # Dictionary with Encodings

        if getFolderSize("Encodings/") != len(encodingNames):
            import EncodingModel

        encodingList = toList(faceEncodingsKnown)
        for x in range(0, int(len(encodingList))):
            encodingList[x] = np.load("Encodings/" + str(encodingNames[x]))

    def addFace(self):
        global dynamicState, encodingNames, fullStudentNames, faceNamesKnown, encodingList, frame
        print("hello")
        if 'Samrat' in faceNames and len(faceLocations) > 1:
            dynamicAdd(frame)
            fullStudentNames = loadLists("List Information/Full Student Names")  # List with full Student Names
            faceNamesKnown = loadLists("List Information/Face Names Known")  # List With Face Names
            encodingNames = loadLists("List Information/Encoding Names")  # List With encoding names
            loadDictionary("List Information/Face Names Known", faceEncodingsKnown)  # Dictionary with Encodings

            if getFolderSize("Encodings/") != len(encodingNames):
                import EncodingModel

            encodingList = toList(faceEncodingsKnown)
            for x in range(0, int(len(encodingList))):
                encodingList[x] = np.load("Encodings/" + str(encodingNames[x]))
            dynamicState = False

    def getRawFrame(self):
        _, frameToReturn = self.video.read()
        return frameToReturn

    def getFrame(self):
        try:
            global processThisFrame, faceLocations, faceNames, encodingList, faceNamesKnown, fullStudentNames
            global model, inputFrames, frame, dynamicState

            success, frame = self.video.read()
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time
            if processThisFrame:
                # Find all the faces and face encodings in the current frame of video
                faceLocations = face_recognition.face_locations(rgb_small_frame)
                faceEncodings = face_recognition.face_encodings(rgb_small_frame, faceLocations)

                faceNames = []
                blurAmount = cv2.Laplacian(frame, cv2.CV_64F).var()
                if blurAmount > 40:
                    for faceEncoding in faceEncodings:
                        # See if the face is a match for the known face(s)
                        matchesFound = face_recognition.compare_faces(encodingList, faceEncoding)
                        name = "Unknown"

                        # Or instead, use the known face with the smallest distance to the new face
                        faceDistances = face_recognition.face_distance(encodingList, faceEncoding)
                        matchIndex = np.argmin(faceDistances)
                        if matchesFound[matchIndex]:
                            name = faceNamesKnown[matchIndex]

                        faceNames.append(name)

            processThisFrame = not processThisFrame

            # Display the results
            for (top, right, bottom, left), name in zip(faceLocations, faceNames):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (255, 0, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                blurAmount = cv2.Laplacian(frame, cv2.CV_64F).var()
                # livenessVal = getLivenessValue(frame, inputFrames, model)
                if 0.51 > 0.50:
                    if blurAmount > 40:
                        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                else:
                    cv2.putText(frame, "WARNING: SPOOF DETECTED", (100, 75), font, 1.0, (0, 0, 255), 2)

                for x in range(0, len(fullStudentNames)):
                    if name in fullStudentNames[x]:
                        updatePresentPersonExcel(fullStudentNames[x])

                for x in range(0, len(faceNamesKnown)):
                    checkIfHere(name, faceNamesKnown[x])

            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()
        except Exception as e:
            exceptionType, exceptionObject, exceptionThrowback = sys.exc_info()
            fileName = os.path.split(exceptionThrowback.tb_frame.f_code.co_filename)[1]
            print(exceptionType, fileName, exceptionThrowback.tb_lineno)
            print(e)