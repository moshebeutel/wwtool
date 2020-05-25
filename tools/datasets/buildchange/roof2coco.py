import argparse

import os
import cv2
import json
import csv
import shutil
import numpy as np
import xml.etree.ElementTree as ET

import wwtool
from wwtool.datasets import Convert2COCO

class SIMPLETXT2COCO(Convert2COCO):
    def __generate_coco_annotation__(self, annotpath, imgpath):
        """
        docstring here
            :param self: 
            :param annotpath: the path of each annotation
            :param return: dict()  
        """
        objects = self.__simpletxt_parse__(annotpath, imgpath)
        
        coco_annotations = []

        for object_struct in objects:
            bbox = object_struct['bbox']
            segmentation = object_struct['segmentation']
            label = object_struct['label']

            width = bbox[2]
            height = bbox[3]
            area = height * width

            if area <= self.small_object_area and self.groundtruth:
                self.small_object_idx += 1
                continue

            coco_annotation = {}
            coco_annotation['bbox'] = bbox
            coco_annotation['segmentation'] = [segmentation]
            coco_annotation['category_id'] = label
            coco_annotation['area'] = np.float(area)

            coco_annotations.append(coco_annotation)

        return coco_annotations
    
    def __simpletxt_parse__(self, label_file, image_file):
        """
        (xmin, ymin, xmax, ymax)
        """
        image_basename = wwtool.get_basename(image_file)
        origin_image_name = image_basename.split('__')[0].split(sub_fold + '_')[1]
        # print(image_name_list, origin_image_name)
        if origin_image_name not in image_name_list:
            # print("===========================================")
            return []

        with open(label_file, 'r') as f:
            lines = f.readlines()
    
        objects = []
        total_object_num = 0

        for line in lines:
            object_struct = {}
            line = line.rstrip().split(' ')
            label = " ".join(line[-1])
            mask = [float(_) for _ in line[0:-1]]

            xmin, ymin, xmax, ymax = wwtool.pointobb2bbox(mask)
            bbox_w = xmax - xmin
            bbox_h = ymax - ymin

            total_object_num += 1

            object_struct['bbox'] = [xmin, ymin, bbox_w, bbox_h]
            object_struct['segmentation'] = mask
            object_struct['label'] = 1
            
            objects.append(object_struct)
        
        return objects

def parse_args():
    parser = argparse.ArgumentParser(description='MMDet test detector')
    parser.add_argument(
        '--imagesets',
        type=str,
        nargs='+',
        choices=['trainval', 'test'])
    parser.add_argument(
        '--release_version', default='v1', type=str)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()

    # basic dataset information
    info = {"year" : 2019,
                "version" : "1.0",
                "description" : "SIMPLETXT-Building-COCO",
                "contributor" : "Jinwang Wang",
                "url" : "jwwangchn.cn",
                "date_created" : "2019"
            }
    
    licenses = [{"id": 1,
                    "name": "Attribution-NonCommercial",
                    "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
                }]

    original_simpletxt_class = {'building': 1}

    converted_simpletxt_class = [{'supercategory': 'none', 'id': 1,  'name': 'building',                   }]

    # dataset's information
    image_format='.png'
    anno_format='.txt'

    core_dataset_name = 'buildchange'
    # cities = ['shanghai']
    # sub_city_folds = {'shanghai': ['arg']}
    cities = ['shanghai', 'beijing', 'jinan', 'haerbin', 'chengdu']
    sub_city_folds = {'beijing': ['arg', 'google', 'ms', 'tdt'],
                         'chengdu': ['arg', 'google', 'ms', 'tdt'],
                         'haerbin': ['arg', 'google', 'ms'],
                         'jinan': ['arg', 'google', 'ms', 'tdt'],
                         'shanghai': ['arg', 'google', 'ms', 'tdt', 'PHR2016', 'PHR2017']}
    release_version = 'v2'
    groundtruth = True

    for imageset in ['train', 'val']:
        for idx, city in enumerate(cities):
            if imageset == 'train':
                imageset_file = './data/{}/{}/{}/trainset.txt'.format(core_dataset_name, release_version, city)
            else:
                imageset_file = './data/{}/{}/{}/valset.txt'.format(core_dataset_name, release_version, city)

            image_name_list = []
            imageset_handle = open(imageset_file, 'r')
            image_name_lines = imageset_handle.readlines()
            for image_name_line in image_name_lines:
                image_name_line = image_name_line.strip('\n')
                image_name_list.append(image_name_line)

            for sub_fold in sub_city_folds[city]:
                anno_name = [core_dataset_name, release_version, imageset, city, sub_fold]
                
                imgpath = './data/{}/{}/{}/{}/images'.format(core_dataset_name, release_version, city, sub_fold)
                annopath = './data/{}/{}/{}/{}/labels'.format(core_dataset_name, release_version, city, sub_fold)
                save_path = './data/{}/{}/coco/annotations'.format(core_dataset_name, release_version)
                if not os.path.exists(save_path):
                    os.makedirs(save_path)

                simpletxt2coco = SIMPLETXT2COCO(imgpath=imgpath,
                                                annopath=annopath,
                                                image_format=image_format,
                                                anno_format=anno_format,
                                                data_categories=converted_simpletxt_class,
                                                data_info=info,
                                                data_licenses=licenses,
                                                data_type="instances",
                                                groundtruth=groundtruth,
                                                small_object_area=0)

                images, annotations = simpletxt2coco.get_image_annotation_pairs()

                json_data = {"info" : simpletxt2coco.info,
                            "images" : images,
                            "licenses" : simpletxt2coco.licenses,
                            "type" : simpletxt2coco.type,
                            "annotations" : annotations,
                            "categories" : simpletxt2coco.categories}

                with open(os.path.join(save_path, "_".join(anno_name) + ".json"), "w") as jsonfile:
                    json.dump(json_data, jsonfile, sort_keys=True, indent=4)

            imageset_handle.close()
