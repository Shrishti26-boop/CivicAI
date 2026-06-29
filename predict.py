import json
import cv2
import numpy as np
import tensorflow as tf

IMG_SIZE = 224

# Load model only once
model = tf.keras.models.load_model("best_model.keras")

# Load class names
with open("classes.json", "r") as f:
    classes = json.load(f)


def predict(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return None, 0.0

    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    prediction = model.predict(img, verbose=0)

    index = np.argmax(prediction)
    confidence = float(np.max(prediction))

    print("Prediction:", prediction)
    print("Class:", classes[index])
    print("Confidence:", confidence)

    # return dummy output for deployment
    return "pothole"