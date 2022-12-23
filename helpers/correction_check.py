import os
import pickle

from constants import *
from PIL import Image

from helpers.checking_functions import check_copy_paste_from_assingment, copy_pasted_candidates_to_csv
from mask_aggregations import get_image_to_adjust


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



if __name__ == "__main__":

    # check_only_masks_in_dir()
    find_correction_without_annotation()