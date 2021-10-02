# -*- coding: utf-8 -*-
"""Opti-Trial.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rQKwdsuQz4C7h0Fw64ut62oAW5ttAVqo
"""

import math
import os
import random

import cv2 
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.python.keras.utils.np_utils import to_categorical
from skimage.transform import rotate
from sklearn.utils import shuffle

"""## Get files from a path"""


def get_files(path):
    files = list()

    # /content/drive/MyDrive/OptiTrials
    for dirname, _, filenames in os.walk(path):
        for filename in filenames:
            files.append(os.path.join(dirname, filename))

    return files



train_files_path = get_files('/Users/admin/Desktop/RICKY SCHOOL/Opti techniques/OptiTrial/Train Dataset')

train_csv = pd.read_csv('/Users/admin/Desktop/RICKY SCHOOL/Opti techniques/OptiTrial/FruitData_training.csv')

print("Train files : {0}".format(len(train_files_path)))

train_dict = dict(zip(train_csv.Images, train_csv.TargetOutput))
print(train_dict['frame 107.jpg'])

"""### Split into training and validation set"""

split = int(len(train_files_path) * 0.83)
random.shuffle(train_files_path)
train_files = train_files_path[:split]
val_files = train_files_path[split:]

print("Training files {0}".format(len(train_files)))
print("Validation files {0}".format(len(val_files)))

"""### Converting dance forms into numbers"""

unique_labels = list(set(train_dict.values()))
unique_labels_mapping = dict()
for index in range(len(unique_labels)):
    unique_labels_mapping[unique_labels[index]] = index

total_classes = len(unique_labels)
print("Number of classes : {0}".format(total_classes))


def get_one_hot_encoded_mask(value, num_labels):
    return to_categorical(value, num_classes=num_labels)


"""### Setting up hyper-parameters"""

img_width, img_height = 256, 256
batch_size = 16
epochs = 10
learning_rate = 1e-3

"""### Creating Augmentations"""


def rotate_image(image, angle_list):
    rotated_images = list()
    for angle in angle_list:
        rotated_images.append(rotate(image, angle))

    return rotated_images


def scaleDown_image(image, fx=0.6, fy=0.6):
    return cv2.resize(image, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_LINEAR)


def scaleUp_image(image, fx=2, fy=2):
    return cv2.resize(image, None, fx=fx, fy=fy, interpolation=cv2.INTER_LINEAR)


def horizontal_flip(img):
    return img[:, ::-1]


def blur(img, kernel=(5, 5)):
    return cv2.GaussianBlur(img, kernel, 0)


def brightness(img, low=-50, high=50):
    brightness = np.random.randint(low, high)
    img = img + brightness
    return img


"""## Creating DataGenerator"""


class DataGenerator:
    def __init__(self, train_files, valid_files, labels_dict, batch_size=16, val_augment=True):
        self.train_files = train_files
        self.valid_files = valid_files
        self.labels_dict = labels_dict
        self.batch_size = batch_size
        self.val_augment = val_augment

    def train_generator(self):
        num_images = len(self.train_files)
        while True:
            x_batch = list()
            y_batch = list()
            index_list = list(range(0, num_images))
            index_list = shuffle(index_list)
            for idxs in range(0, num_images, self.batch_size):
                x_batch = list()
                y_batch = list()
                for idx in index_list[idxs:min(idxs + self.batch_size, num_images)]:

                    img = cv2.imread(self.train_files[idx])
                    img = cv2.resize(img, (img_width, img_height))
                    img = img / 255
                    x_batch.append(img)

                    image_name = self.train_files[idx].split("/")
                    label = unique_labels_mapping[train_dict[str(image_name[-1])]]
                    label = get_one_hot_encoded_mask(label, total_classes)
                    y_batch.append(label)

                    rotated_images = rotate_image(img, [45, 60, -45, -60])
                    for rotated_image in rotated_images:
                        x_batch.append(rotated_image)
                        y_batch.append(label)

                    x_batch.append(horizontal_flip(img))
                    y_batch.append(label)

                    x_batch.append(blur(img))
                    y_batch.append(label)

                    x_batch.append(brightness(img))
                    y_batch.append(label)

                x_batch, y_batch = shuffle(x_batch, y_batch, random_state=0)
                yield (np.asarray(x_batch), np.asarray(y_batch))

    def valid_generator(self):
        num_images = len(self.valid_files)
        while True:
            x_batch = list()
            y_batch = list()
            index_list = list(range(0, num_images))
            index_list = shuffle(index_list)
            for idxs in range(0, num_images, self.batch_size):
                x_batch = list()
                y_batch = list()
                for idx in index_list[idxs:min(idxs + self.batch_size, num_images)]:

                    img = cv2.imread(self.valid_files[idx])
                    img = cv2.resize(img, (img_width, img_height))
                    img = img / 255
                    x_batch.append(img)

                    image_name = self.valid_files[idx].split("/")
                    label = unique_labels_mapping[train_dict[str(image_name[-1])]]
                    label = get_one_hot_encoded_mask(label, total_classes)
                    y_batch.append(label)

                    if self.val_augment:
                        rotated_images = rotate_image(img, [45, 60, -45, -60])
                        for rotated_image in rotated_images:
                            x_batch.append(rotated_image)
                            y_batch.append(label)

                        x_batch.append(horizontal_flip(img))
                        y_batch.append(label)

                        x_batch.append(blur(img))
                        y_batch.append(label)

                        x_batch.append(brightness(img))
                        y_batch.append(label)

                x_batch, y_batch = shuffle(x_batch, y_batch, random_state=0)
                yield (np.asarray(x_batch), np.asarray(y_batch))


epoch_steps = int(math.ceil(len(train_files) / batch_size) * 8)
print(epoch_steps)
val_steps = int(math.ceil(len(val_files) / batch_size) * 8)
print(val_steps)

"""## Model Experiments"""

from tensorflow.python.keras.applications import inception_v3
from tensorflow.python.keras.layers import Dense, Flatten, Dropout 
# from keras.optimizers import Adam, SGD
from tensorflow.python.keras.models import Model
import tensorflow.keras as keras
from tensorflow.keras.optimizers import SGD



"""### InceptionV3 Setup"""

base_model = inception_v3.InceptionV3(include_top=False, input_shape=(img_width, img_height, 3),
                                      weights='/Users/admin/Desktop/RICKY SCHOOL/Opti techniques/OptiTrial/inception_v3_weights_tf_dim_ordering_tf_kernels_notop.h5')
x = base_model.output
x = Flatten()(x)
x = Dense(1024, activation='relu')(x)
x = Dropout(0.5)(x)
x = Dense(512, activation='relu')(x)
final_layer = Dense(total_classes, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=final_layer)
model.summary()

model.compile(optimizer=SGD(learning_rate=learning_rate, momentum=0.9),
              loss='categorical_crossentropy', metrics=['accuracy'])

datagen = DataGenerator(train_files, val_files, train_dict, batch_size)


def lr_scheduler(epoch, lr):
    #     if epoch % 2 == 0:
    #         return lr
    return lr * 1.0


callbacks = [
    keras.callbacks.LearningRateScheduler(lr_scheduler),
    #     keras.callbacks.ModelCheckpoint(filepath='/kaggle/working/models.{epoch:03d}.hdf5',
    #                     monitor='loss', verbose=2, save_best_only=False)
]

history = model.fit_generator(generator=datagen.train_generator() , steps_per_epoch=epoch_steps, 
                             epochs=20, validation_steps = val_steps, 
                             validation_data=datagen.valid_generator(), verbose=2, callbacks=callbacks)



"""## Generate Predictions"""

inv_map = {v: k for k, v in unique_labels_mapping.items()}
print(inv_map)

test_csv = pd.read_csv('/content/drive/MyDrive/OptiTrials/Dataset/FruitData_training.csv')

test_images = test_csv['Images']
print(test_images[:5])

output = list()
for index in range(len(test_images)):
    img = cv2.imread('/content/drive/MyDrive/OptiTrials/Dataset//Train Data' + str(test_images[index]))
    img = cv2.resize(img, (img_width, img_height))
    img = img / 255
    img = np.expand_dims(img, axis=0)
    pred = model.predict(img)
    output.append(inv_map[np.argmax(pred)])

df = pd.DataFrame({'Image': test_images,
                   'target': output})
df.to_csv("/content/drive/MyDrive/OptiTrials/Dataset/FruitData_training.csv", index=False)
