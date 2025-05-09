# -*- coding: utf-8 -*-
"""LeNet_Chest_Xray_dataset.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1n90eQ93Ca9X9t4xjt7cwMivHxCX-4NHe
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
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, AveragePooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator

df = pd.read_csv("/content/drive/MyDrive/Chest_Cancer_Dataset/Chest_xray_Corona_Metadata.csv")

train_df = df[df['Dataset_type'] == 'TRAIN'].copy()
test_df = df[df['Dataset_type'] == 'TEST'].copy()

train_path = '/content/drive/MyDrive/Chest_Cancer_Dataset/Coronahack-Chest-XRay-Dataset/Coronahack-Chest-XRay-Dataset/train/'
test_path = '/content/drive/MyDrive/Chest_Cancer_Dataset/Coronahack-Chest-XRay-Dataset/Coronahack-Chest-XRay-Dataset/test/'


train_df['image_path'] = train_path + train_df['X_ray_image_name']
test_df['image_path'] = test_path + test_df['X_ray_image_name']

# Label encode classes
le = LabelEncoder()
train_df['label_encoded'] = le.fit_transform(train_df['Label'])
test_df['label_encoded'] = le.transform(test_df['Label'])
train_df['label_encoded'] = train_df['label_encoded'].astype(str)
test_df['label_encoded'] = test_df['label_encoded'].astype(str)

# Computing class weights
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(train_df['label_encoded'].astype(int)),
    y=train_df['label_encoded'].astype(int)
)
class_weights = dict(enumerate(class_weights))

img_size = (32, 32)
batch_size = 32

train_gen = ImageDataGenerator(rescale=1./255, horizontal_flip=True)
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

# LeNet-5 model
model = Sequential([
    Conv2D(6, kernel_size=(5, 5), activation='relu', input_shape=(32, 32, 3), padding='same'),
    AveragePooling2D(pool_size=(2, 2)),
    Conv2D(16, kernel_size=(5, 5), activation='relu'),
    AveragePooling2D(pool_size=(2, 2)),
    Flatten(),
    Dense(120, activation='relu'),
    Dropout(0.3),
    Dense(84, activation='relu'),
    Dropout(0.3),
    Dense(len(le.classes_), activation='softmax')
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

history = model.fit(
    train_data,
    validation_data=test_data,
    epochs=15,
    class_weight=class_weights
)

# Evaluate the accuracy
loss, accuracy = model.evaluate(test_data)
print(f"Test Accuracy: {accuracy:.4f}")

# Predictions on test dataset which is on chest Xray
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
plt.title("Confusion Matrix (LeNet - Chest X-ray)")
plt.show()

# Accuracy and loss plots
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Val Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.tight_layout()
plt.show()