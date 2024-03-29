# USAGE
# python detect_mask_video.py

# import the necessary packages
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2
import os
from playsound import playsound
from threading import Thread
TRANSPARENCY_ALPHA = 0.3

def detect_and_predict_mask(frame, faceNet, maskNet):
	# grab the dimensions of the frame and then construct a blob
	# from it
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
		(104.0, 177.0, 123.0))

	# pass the blob through the network and obtain the face detections
	faceNet.setInput(blob)
	detections = faceNet.forward()

	# initialize our list of faces, their corresponding locations,
	# and the list of predictions from our face mask network
	faces = []
	locs = []
	preds = []

	# loop over the detections
	for i in range(0, detections.shape[2]):
		# extract the confidence (i.e., probability) associated with
		# the detection
		confidence = detections[0, 0, i, 2]

		# filter out weak detections by ensuring the confidence is
		# greater than the minimum confidence
		if confidence > args["confidence"]:
			# compute the (x, y)-coordinates of the bounding box for
			# the object
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			# ensure the bounding boxes fall within the dimensions of
			# the frame
			(startX, startY) = (max(0, startX), max(0, startY))
			(endX, endY) = (min(w - 1, endX), min(h - 1, endY))

			# extract the face ROI, convert it from BGR to RGB channel
			# ordering, resize it to 224x224, and preprocess it
			face = frame[startY:endY, startX:endX]
			face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
			face = cv2.resize(face, (224, 224))  #
			face = img_to_array(face)
			face = preprocess_input(face)
			face = np.expand_dims(face, axis=0)

			# add the face and bounding boxes to their respective
			# lists
			faces.append(face)
			locs.append((startX, startY, endX, endY))

	# only make a predictions if at least one face was detected
	if len(faces) > 0:
		# for faster inference we'll make batch predictions on *all*
		# faces at the same time rather than one-by-one predictions
		# in the above `for` loop
		preds = maskNet.predict(faces)

	# return a 2-tuple of the face locations and their corresponding
	# locations
	return (locs, preds)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", type=str,
	default="face_detector",
	help="path to face detector model directory")
ap.add_argument("-m", "--model", type=str,
	default="model10.model",
	help="path to trained face mask detector model")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

# load our serialized face detector model from disk
print("[INFO] loading face detector model...")
prototxtPath = os.path.sep.join([args["face"], "deploy.prototxt"])
weightsPath = os.path.sep.join([args["face"],
	"res10_300x300_ssd_iter_140000.caffemodel"])
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

# load the face mask detector model from disk
print("[INFO] loading face mask detector model...")
maskNet = load_model(args["model"])

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

# add timer
no_mask_time = 0
# add image
mask_icon = cv2.imread('mask_icon_150.png', -1)

def add_mask_icon(mask_icon, frame):
	y1, y2 = 50, 50 + mask_icon.shape[0]
	x1, x2 = 320, 320 + mask_icon.shape[1]

	alpha_s = mask_icon[:, :, 3] / 255.0
	alpha_l = 1.0 - alpha_s

	for c in range(0, 3):
		frame[y1:y2, x1:x2, c] = (alpha_s * mask_icon[:, :, c] +
								  alpha_l * frame[y1:y2, x1:x2, c])

# loop over the frames from the video stream
while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	frame = vs.read()
	frame = imutils.resize(frame, width=800)

	# detect faces in the frame and determine if they are wearing a
	# face mask or not
	(locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

	# loop over the detected face locations and their corresponding
	# locations
	for (box, pred) in zip(locs, preds):
		# unpack the bounding box and predictions
		(startX, startY, endX, endY) = box
		(mask, withoutMask) = pred

		# # determine the class label and color we'll use to draw
		# # the bounding box and text
		# label = "Mask" if mask > withoutMask else "No Mask"
		# color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
		#
		# # include the probability in the label
		# label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)
		#
		# # display the label and bounding box rectangle on the output
		# # frame
		# cv2.putText(frame, label, (startX, startY - 10),
		# 	cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
		# cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

		# determine the class label and color we'll use to draw
		# the bounding box
		color = (0, 128, 0) if mask > withoutMask else (0, 0, 255)
		label = "You Look GREAT!" if mask > withoutMask else "Please Wear A Mask!!!"

		if label == "Please Wear A Mask!!!":
			if not no_mask_time:
				no_mask_time = time.time()
			if no_mask_time + 3 < time.time():
				# playsound('beep_short.wav')
				sound_thread = Thread(target=lambda: playsound('beep.wav'))
				sound_thread.start()
				no_mask_time = 0
		else:
			no_mask_time = 0

		overlay = frame.copy()  # transparent background
		# output = frame.copy()  # output frame

		# display the label and bounding box rectangle on the output frame
		if mask > withoutMask:
			cv2.putText(frame, label, (250, 60),
						cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
			cv2.putText(frame, "Thank you for staying safe!", (220, 20),
					cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
		else:
			cv2.putText(frame, label, (40, 70),
						cv2.FONT_HERSHEY_SIMPLEX, 2, color, 5)

			add_mask_icon(mask_icon, frame)
			cv2.rectangle(overlay, (0, 0), (800, 800), color, -1)  # transparent layer
			cv2.addWeighted(overlay, TRANSPARENCY_ALPHA, frame, 1 - TRANSPARENCY_ALPHA, 0, frame)

		cv2.rectangle(frame, (startX, startY), (endX, endY), color, 3)

	# show the output frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break




# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()