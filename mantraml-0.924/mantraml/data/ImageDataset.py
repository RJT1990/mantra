import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import scipy.misc

from .Dataset import Dataset, datamethod


class ImageDataset(Dataset):
    """
    This class implements dataset processing methods for a tabular dataset
    """
    dataset_type = 'images'
    has_labels = False
    normalize = True

    def __init__(self, **kwargs):       
        """
        This initialises an instance of an Image Dataset
        """

        # user specified training_test_split
        
        super().__init__(**kwargs)

    @datamethod
    def X(self):
        """
        This method extracts inputs from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Returns
        --------
        np.ndarray - of data inputs (X vector)
        """

        images = glob.glob(os.path.join(self.extracted_data_path, '*%s' % self.file_format))

        training_data = []
        self.unprocessed_images = []
        self.image_file_names = []

        for image_name in images:
            image_data = self.get_image(image_name, resize_height=self.image_shape[0], 
                resize_width=self.image_shape[1], crop=True, normalize=self.normalize)
            if image_data.shape == self.image_shape:
                training_data.append(image_data)
                self.image_file_names.append(image_name.split(self.extracted_data_path +'/')[-1])
            else:
                self.unprocessed_images.append((image_name, 'Image shape of extracted image differed from self.image_shape : %s' % image_name))

        return np.array(training_data)

    @classmethod
    def imread(cls, path, grayscale = False):
        """
        This method reads an image from path

        Parameters
        ----------
        path - str
            Location of the image

        grayscale - bool
            Whether the image is greyscale or not

        Returns
        ----------
        np.ndarray - representation of the image
        """

        if grayscale:
            return scipy.misc.imread(path, flatten = True).astype(np.float)
        else:
            return scipy.misc.imread(path).astype(np.float)

    @classmethod
    def center_crop(cls, image, resize_height=64, resize_width=64):
        """
        This method center crops an image and resizes 

        Parameters
        ----------
        resize_height - int
            Height of the image in pixels

        resize_width - int
            Width of the image in pixels

        Returns
        ----------
        np.ndarray - resized image
        """

        h, w = image.shape[:2]

        if h > w:
            divisor = int((h - w) / 2)
            if divisor:
                image = image[divisor:-divisor,:,:]
        elif w > h:
            divisor = int((w - h) / 2)
            if divisor:
                image = image[:,divisor:-divisor,:]

        return scipy.misc.imresize(image, [resize_height, resize_width])

    @classmethod
    def get_image(cls, path, resize_height=64, resize_width=64, crop=True, grayscale=False, normalize=True):
        """
        This method gets an image from a path and applies a transformation

        Parameters
        ----------
        resize_height - int
            Height of the image in pixels

        resize_width - int
            Width of the image in pixels

        crop - bool
            If true, applies a crop to the image

        grayscale - bool
            If true, load the image as greyscale

        normalize - bool
            If true, centers the image values around 0 (for learning)

        Returns
        ----------
        np.ndarray - resized image
        """

        image = cls.imread(path, grayscale)
        
        return cls.transform(image, resize_height, resize_width, crop, normalize=normalize)

    @classmethod
    def transform(cls, image, resize_height=64, resize_width=64, crop=True, normalize=True):
        """
        This method gets an image from a path and applies a transformation

        Parameters
        ----------
        image - np.ndarray
            The image to apply the transformation to

        resize_height - int
            Height of the image in pixels

        resize_width - int
            Width of the image in pixels

        crop - bool
            If true, applies a crop to the image

        normalize - bool
            If true, centers the image values around 0 (for learning)

        Returns
        ----------
        np.ndarray - resized image
        """

        if crop:
            cropped_image = cls.center_crop(image, resize_height, resize_width)
        else:
            cropped_image = scipy.misc.imresize(image, [resize_height, resize_width])

        if normalize:
            return np.array(cropped_image)/127.5 - 1.
        else:
            return np.array(cropped_image)