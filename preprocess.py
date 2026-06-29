import os
import cv2
import random

# ===========================
# SETTINGS
# ===========================

INPUT_DATASET = "dataset"
OUTPUT_DATASET = "processed_dataset"

IMG_SIZE = 224
IMAGES_PER_CLASS = 1000

# ===========================
# Create output folder
# ===========================

os.makedirs(OUTPUT_DATASET, exist_ok=True)

classes = [
    c for c in os.listdir(INPUT_DATASET)
    if os.path.isdir(os.path.join(INPUT_DATASET, c))
]

print("Classes:", classes)

# ===========================
# Process each class
# ===========================

for cls in classes:

    input_folder = os.path.join(INPUT_DATASET, cls)
    output_folder = os.path.join(OUTPUT_DATASET, cls)

    os.makedirs(output_folder, exist_ok=True)

    image_paths = []

    # Find images recursively
    for root, dirs, files in os.walk(input_folder):

        for file in files:

            if file.lower().endswith((".jpg", ".jpeg", ".png")):

                image_paths.append(
                    os.path.join(root, file)
                )

    print(f"{cls}: {len(image_paths)} images found")

    # Shuffle
    random.shuffle(image_paths)

    # Limit
    image_paths = image_paths[:IMAGES_PER_CLASS]

    count = 0

    for path in image_paths:

        img = cv2.imread(path)

        if img is None:
            continue

        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

        save_path = os.path.join(
            output_folder,
            f"{count}.jpg"
        )

        cv2.imwrite(save_path, img)

        count += 1

    print(f"{cls}: {count} images saved")