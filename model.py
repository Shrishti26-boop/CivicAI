import json
import numpy as np
import tensorflow as tf

from dataset_loader import load_data
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# ===========================
# Load Dataset
# ===========================

X, y, class_names = load_data("processed_dataset")

print("Classes:", class_names)
print("Dataset Shape:", X.shape)

# Normalize
X = X.astype("float32") / 255.0

# ===========================
# Save Class Names
# ===========================

with open("classes.json", "w") as f:
    json.dump(class_names, f)

# ===========================
# Train Test Split
# ===========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ===========================
# Class Weights
# ===========================

weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(y_train),
    y=y_train
)

class_weights = dict(enumerate(weights))

print("Class Weights:", class_weights)

# ===========================
# CNN Model
# ===========================

model = tf.keras.Sequential([

    tf.keras.layers.Input(shape=(224,224,3)),

    tf.keras.layers.Conv2D(32,3,padding="same",activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(64,3,padding="same",activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(128,3,padding="same",activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Flatten(),

    tf.keras.layers.Dense(256,activation="relu"),
    tf.keras.layers.Dropout(0.5),

    tf.keras.layers.Dense(128,activation="relu"),
    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(len(class_names),activation="softmax")

])

# ===========================
# Compile
# ===========================

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# ===========================
# Callbacks
# ===========================

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=3,
    restore_best_weights=True
)

checkpoint = ModelCheckpoint(
    "best_model.keras",
    monitor="val_accuracy",
    save_best_only=True,
    verbose=1
)

# ===========================
# Train
# ===========================

history = model.fit(
    X_train,
    y_train,
    validation_data=(X_test,y_test),
    epochs=20,
    class_weight=class_weights,
    callbacks=[early_stop,checkpoint]
)

# ===========================
# Evaluation
# ===========================

loss, accuracy = model.evaluate(X_test,y_test)

print("\n==========================")
print("Final Accuracy :", accuracy)
print("Final Loss     :", loss)
print("==========================")

# ===========================
# Save Final Model
# ===========================

model.save("civic_ai_model.keras")

print("\n✅ Model Saved Successfully")
print("✅ Best Model : best_model.keras")
print("✅ Final Model: civic_ai_model.keras")
print("✅ Classes Saved: classes.json")