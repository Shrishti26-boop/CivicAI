import os
import cv2
import numpy as np

IMG_SIZE = 224

def load_data(dataset_path):

    data = []
    labels = []
    class_names = []

    classes = sorted([
        c for c in os.listdir(dataset_path)
        if os.path.isdir(os.path.join(dataset_path, c))
    ])

    print("Classes:", classes)

    for label, cls in enumerate(classes):

        class_names.append(cls)

        folder = os.path.join(dataset_path, cls)

        for file in os.listdir(folder):

            if not file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            path = os.path.join(folder, file)

            img = cv2.imread(path)

            if img is None:
                continue

            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

            data.append(img)
            labels.append(label)

    return np.array(data), np.array(labels), class_names