import os
import pickle

import numpy as np

from constants import *
from PIL import Image

from helpers.checking_functions import check_copy_paste_from_assingment, copy_pasted_candidates_to_csv, \
    check_mask_connected
from mask_aggregations import get_image_to_adjust, get_images_to_adjust_from_corrected_but_not_anotated


def find_correction_without_annotation():
    to_check = os.listdir(ANNOTATIONS_PATH)
    to_check.extend(os.listdir(LARGE_UPLOADS_PATH))

    without_annotations = {"none": []}
    annotated = get_image_to_adjust()

    for user in to_check:
        # check directory
        user_dir = os.path.join(ANNOTATIONS_PATH, user, "masks")
        if not os.path.exists(user_dir):
            user_dir = os.path.join(LARGE_UPLOADS_PATH, user, "masks")
        if not os.path.exists(user_dir):
            print(f"User {user} has no masks")
            continue
        for dir in os.listdir(user_dir):
            dir_path = os.path.join(user_dir, dir)
            if not os.path.isdir(dir_path):
                continue
            # for all the files in the directory, load them as image and check if only black and white
            for file in os.listdir(dir_path):

                key = (dir, file[:-4])
                if key not in annotated:
                    print(f"{key} is not in annotated")
                    without_annotations["none"].append((key, user))
                    continue

                annotators = [x[0] for x in annotated[key]]
                if user not in annotators:
                    print(f"{user} did not annotate {key}")
                    if user not in without_annotations:
                        without_annotations[user] = []
                    without_annotations[user].append(key)
    missers = {}
    for name in without_annotations:
        if name == "none":
            continue
        if name not in missers:
            missers[name] = 0
        missers[name] += 1

    for x in without_annotations["none"]:
        name = x[1]
        if name not in missers:
            missers[name] = 0
        missers[name] += 1

    print(without_annotations)
    # check_copy_paste_from_assingment(without_annotations["none"])
    copy_pasted_candidates_to_csv(without_annotations["none"])

    # store_mistakes(missers, "provided corrections without annotation")


def annotations_to_annotations_by_user():
    annotations = get_image_to_adjust()
    annotations_by_user = {}
    for key in annotations:
        for annotation in annotations[key]:
            user = annotation[0]
            if user not in annotations_by_user:
                annotations_by_user[user] = set()
            annotations_by_user[user].add(key)
    return annotations_by_user

def check_uncorrected_mistake():
    # check if there are any mistakes that are not corrected

    # get annotations
    annotations = annotations_to_annotations_by_user()

    counter_not_anot = {}
    counter_anot = {}

    # pass folders in ANNOTATIONS_PATH
    for student_name in annotations:
        for image in annotations[student_name]:

            # try to find image in annotations
            image_path1 = os.path.join(ANNOTATIONS_PATH, student_name, "masks", image[0], image[1] + ".png")

            # try to find image in large uploads
            image_path2 = os.path.join(LARGE_UPLOADS_PATH, student_name, "masks", image[0], image[1] + ".png")

            # check if image exists
            if os.path.exists(image_path1) or os.path.exists(image_path2):
                if student_name not in counter_anot:
                    counter_anot[student_name] = 0
                counter_anot[student_name] += 1
            else:
                if student_name not in counter_not_anot:
                    counter_not_anot[student_name] = 0
                counter_not_anot[student_name] += 1

    store_mistakes(counter_not_anot, "not corrected, but annotated, mistakes")
    # store_mistakes(counter_anot, "corrected annotated, mistakes")


def check_all_images_only_one_mask():
    to_check = os.listdir(ANNOTATIONS_PATH)
    to_check.extend(os.listdir(LARGE_UPLOADS_PATH))

    discnotecs_report = {}


    for user in to_check:
        # check directory
        user_dir = os.path.join(ANNOTATIONS_PATH, user, "masks")

        if not os.path.exists(user_dir):
            user_dir = os.path.join(LARGE_UPLOADS_PATH, user, "masks")

        if not os.path.exists(user_dir):
            print(f"User {user} has no masks")
            continue

        for masks_dir in os.listdir(user_dir):
            masks_dir_path = os.path.join(user_dir, masks_dir)

            if not os.path.isdir(masks_dir_path):
                continue

            for mask in os.listdir(masks_dir_path):

                mask_path = os.path.join(masks_dir_path, mask)
                if "png" not in mask_path:
                    continue

                # load mask
                mask_img = Image.open(mask_path)
                # to grayscale
                mask_img = mask_img.convert("L")

                # get white indexes
                white_indexes = np.where(np.array(mask_img) == 255)

                if len(white_indexes[0]):
                    if not check_mask_connected(white_indexes):
                        print(f"Mask {mask_path} is not connected")

                        if user not in discnotecs_report:
                            discnotecs_report[user] = 0
                        discnotecs_report[user] += 1


                else:
                    print(f"Mask {mask_path} has no mask")

    store_mistakes(discnotecs_report, "Number of disconetc masks")

if __name__ == "__main__":

    # check_only_masks_in_dir()
    # get_images_to_adjust_from_corrected_but_not_anotated()
    # check_uncorrected_mistake()

    check_all_images_only_one_mask()