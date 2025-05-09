# -*- coding: utf-8 -*-
"""DenseNet_Chest_Xray.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/11xkwo_WIBaCXuDRTKwUtA_RsuiGPpa1n
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.models import Model
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Load metadata
df = pd.read_csv("/content/drive/MyDrive/archive.zip (Unzipped Files)/Chest_xray_Corona_Metadata.csv")

# Manually set base paths
train_base_path = "/content/drive/MyDrive/archive.zip (Unzipped Files)/Coronahack-Chest-XRay-Dataset/Coronahack-Chest-XRay-Dataset/train"
test_base_path = "/content/drive/MyDrive/archive.zip (Unzipped Files)/Coronahack-Chest-XRay-Dataset/Coronahack-Chest-XRay-Dataset/test"

# Filter by dataset type
train_df = df[df['Dataset_type'] == 'TRAIN'].copy()
test_df = df[df['Dataset_type'] == 'TEST'].copy()

# Add static full image paths using apply
train_df['image_path'] = train_df['X_ray_image_name'].apply(lambda x: os.path.join(train_base_path, x))
test_df['image_path'] = test_df['X_ray_image_name'].apply(lambda x: os.path.join(test_base_path, x))

# Encode labels
le = LabelEncoder()
train_df['label_encoded'] = le.fit_transform(train_df['Label']).astype(str)
test_df['label_encoded'] = le.transform(test_df['Label']).astype(str)

# Class weights
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(train_df['label_encoded'].astype(int)),
    y=train_df['label_encoded'].astype(int)
)
class_weights = dict(enumerate(class_weights))

# Image generators
img_size = (224, 224)
batch_size = 32
train_gen = ImageDataGenerator(rescale=1./255, horizontal_flip=True, zoom_range=0.2)
test_gen = ImageDataGenerator(rescale=1./255)

train_data = train_gen.flow_from_dataframe(
    train_df,
    x_col='image_path',
    y_col='label_encoded',
    target_size=img_size,
    class_mode='sparse',
    batch_size=batch_size
)

test_data = test_gen.flow_from_dataframe(
    test_df,
    x_col='image_path',
    y_col='label_encoded',
    target_size=img_size,
    class_mode='sparse',
    batch_size=batch_size,
    shuffle=False
)

# Build DenseNet121
base_model = DenseNet121(include_top=False, weights='imagenet', input_shape=(224, 224, 3))
base_model.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.3)(x)
out = Dense(len(le.classes_), activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=out)
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Train top layers
history = model.fit(
    train_data,
    validation_data=test_data,
    epochs=5,
    class_weight=class_weights
)

# Fine-tune entire model
base_model.trainable = True
model.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

history_finetune = model.fit(
    train_data,
    validation_data=test_data,
    epochs=5,
    class_weight=class_weights
)

# Evaluate
loss, acc = model.evaluate(test_data)
print(f"Test Accuracy (Fine-Tuned): {acc:.4f}")

# Classification
y_true = test_data.classes
y_probs = model.predict(test_data)
y_pred = np.argmax(y_probs, axis=1)
class_labels = list(le.classes_)

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=class_labels))

cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_labels, yticklabels=class_labels)
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix (DenseNet - Chest X-ray)")
plt.show()

# Accuracy/Loss Graphs
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Acc (Initial)')
plt.plot(history.history['val_accuracy'], label='Val Acc (Initial)')
plt.plot(range(len(history_finetune.history['accuracy'])), history_finetune.history['accuracy'], label='Train Acc (Fine-Tune)')
plt.plot(range(len(history_finetune.history['val_accuracy'])), history_finetune.history['val_accuracy'], label='Val Acc (Fine-Tune)')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss (Initial)')
plt.plot(history.history['val_loss'], label='Val Loss (Initial)')
plt.plot(range(len(history_finetune.history['loss'])), history_finetune.history['loss'], label='Train Loss (Fine-Tune)')
plt.plot(range(len(history_finetune.history['val_loss'])), history_finetune.history['val_loss'], label='Val Loss (Fine-Tune)')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.tight_layout()
plt.show()