# Importh the necessary libraries
import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load the pre-trained model
model = load_model("final_model.h5")

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Map numbers from the model's prediction to emotion labels
emotions = {0: "Angry", 1: "Disgust", 2: "Fear", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprise"}

# Create a class to handle video streaming
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    # capture and process frames
    def get_frame(self):
        ret, frame = self.video.read()
        if not ret:
            return None
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Detect faces in the frame
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        # process each detected faces
        for (x, y, w, h) in faces:
            # crop the detected face
            face_detect=gray[y:y + h, x:x + w] 
            # resize the cropped face
            roi = cv2.resize(face_detect, (48, 48), interpolation=cv2.INTER_AREA)
            # Normalize the ROI
            normalize=roi/255.0
            # Reshape the image to 1 batch size to match the input of the model
            reshaped=normalize.reshape(1, 48, 48, 1)
            # Make a prediction using the model
            prediction=model.predict(reshaped)
            # find the index of the highest probability
            label=np.argmax(prediction, axis=1)[0]
            # Convert to the label
            emotion_text=emotions[label]

            # Draw bounding box and label
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, emotion_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)     

        #Encode frame as JPEG for real-time processing
        ret, jpg = cv2.imencode('.jpg', frame)
        return jpg.tobytes()

def process_image(image_path, output_path):
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        # Return None if image is invalid
        return None

   # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face_detect=gray[y:y + h, x:x + w] 
        # Extract the face region of interest (ROI) from the image
        roi = cv2.resize(face_detect, (48, 48), interpolation=cv2.INTER_AREA)
        # Normalize the ROI
        normalize=roi/255.0
        # Reshape the image to match the input of the model
        reshaped=normalize.reshape(1, 48, 48, 1)
        # Make a prediction using the model
        prediction=model.predict(reshaped)
        label=np.argmax(prediction, axis=1)[0]
        emotion_text=emotions[label]

        # Draw bounding box and label
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(image, emotion_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)     

    # save the processed image
    cv2.imwrite(output_path, image)
    return output_path