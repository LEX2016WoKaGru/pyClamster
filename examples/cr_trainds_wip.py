# -*- coding: utf-8 -*-
"""
Created on 02.06.16

Created for pyclamster


    Copyright (C) {2016}

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# System modules
import os
import glob
import pickle
import time

# External modules
import scipy
import numpy as np
import sklearn.cluster

# Internal modules
import pyclamster as pycl
from pyclamster.clustering.Labels import Labels
#from pyclamster.clustering.kmeans import KMeans
from pyclamster.clustering.functions import localBrightness, rbDetection,\
    listShuffleSplit

__version__ = "doesnt working!"

"""
At the moment only a container for ideas!
Script to create the training dataset for the supervised cloud detection
algorithm with an unsupervised approach.

# TODO if it is working, check with big data and memory!
Possible new version of k-means necessary.
"""

directory = "./images/stereo"
all_images = glob.glob(os.path.join(directory, "*.jpg"))
k_cluster = 2

concated_images = None
labels = None

targets = []
mini_images= []
cluster = sklearn.cluster.MiniBatchKMeans(n_clusters=k_cluster, random_state=0)
used_labels = 0

all_images = listShuffleSplit(all_images, 10)
for image_list in all_images:
    for image_path in image_list:
        img = pycl.Image(image_path)
        """
        Here comes some pre-process corrections, like projection correction etc.
        """
        img.data=localBrightness(img.data)
        img.crop((480, 480, 1440, 1440))
        img_data = rbDetection(img.data)
        w, h = original_shape = tuple(img_data.shape)
        if concated_images is None:
            concated_images = np.reshape(img_data, (w * h, 1))
        else:
            concated_images = np.r_[concated_images,
                                    np.reshape(img_data, (w * h, 1))]
    #print(concated_images.shape)
    start_time = time.time()
    cluster.partial_fit(concated_images)
    print(concated_images.shape[0], time.time()-start_time)
    labels = Labels(cluster.labels_[used_labels:])
    used_labels = len(cluster.labels_)
    splitted_labels = labels.splitUp(indices_or_sections=len(image_list))
    for key, label in enumerate(splitted_labels):
        label.reshape((w, h), replace=True)
        start_time = time.time()
        label.filterRelevants(10, True)
        positions, y = label.getLabelSamples()
        targets += y
        img = pycl.Image(image_list[key])
        for coord in positions:
            mini_images.append(img.nbCrop(coord, neighbourhood_size=10))

# training_data = {"X": mini_images, "y": targets}
# pickle.dump(training_data, open("training.p", "wb"))
