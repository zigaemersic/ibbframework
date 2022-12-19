import json
import os
import pickle

import cv2
import numpy as np

IMGS_PATH = "/home/petrsejvl/ibb_data/images-zips"
MASKS_PATH = "/home/petrsejvl/ibb_data/masks-zips"
ANNOTATIONS_PATH = "/home/petrsejvl/ibb_data/annotations"
LARGE_UPLOADS_PATH = "/home/petrsejvl/ibb_data/large uploads"
ONLY_MASKS_CORRECTION_PATH = "/home/petrsejvl/ibb_data/only_mask_correction"
ignore_list = [
    "tz7284@student.uni-lj.si",
    "zr13891@student.uni-lj.si",
    "it8816@student.uni-lj.si",
    "jb3976@student.uni-lj.si",
    "jf6340@student.uni-lj.si",
    "jm85537@student.uni-lj.si",
    "ls3453@student.uni-lj.si",
    "mb3926@student.uni-lj.si",
    "mc4857@student.uni-lj.si",
    "mm7522@student.uni-lj.si",
    "ms0181@student.uni-lj.si",
    "nv6920@student.uni-lj.si",
    "zh0444@student.uni-lj.si",
    "fd8651@student.uni-lj.si",
    "jp32669@student.uni-lj.si",
    "jv4739@student.uni-lj.si"
]

def get_image_to_adjust():
    to_correct = {}

    # pass files in annotations folder
    for student_name in os.listdir(ANNOTATIONS_PATH):

        csv_path = os.path.join(ANNOTATIONS_PATH, student_name, f"{student_name}.csv")

        # read csv file

        with open(csv_path, "r") as f:
            data = f.readlines()


        # todo ingnore first line only if cannot be converted to integer
        # data = data[1:] if data[0][0]

        for line in data[1:]:
            splitted = line.split(";")

            if len(splitted) <= 5 or splitted[5] == "\n" or splitted[5] == "":
                continue

            if len(splitted) == 7:
                folder, img, _, _, s, m, _ = splitted
            else:
                folder, img, _, _, s, m = splitted
                m = m.strip()

            if len(img) == 3:
                img = img[1:]

            if "/" in img:
                img = img.split("/")[1]

            if (folder, img) not in to_correct:
                to_correct[(folder, img)] = []
            to_correct[(folder, img)].append((student_name, m, s.strip()))

    # returns a dictionary, where the key is  (folder, img) and the value is a list of tuples (student_name, message)
    return to_correct


def check_mask_connected(mask_white_indexes):
    """
    Functions checks if there is exactly one ear mask
    checks that from each point in the mask, you can get to any other point of the mask
    """
    coords = set(zip(mask_white_indexes[0], mask_white_indexes[1]))

    visited = set()
    to_visit = [list(coords)[0]]

    while len(to_visit):
        x, y = to_visit.pop()
        if (x, y) in visited:
            continue  # already visited
        visited.add((x, y))

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if (x + dx, y + dy) in coords:
                to_visit.append((x + dx, y + dy))

    return len(visited) == len(coords)


def visu_image_and_mask(folder, name):
    img_full_path = os.path.join(IMGS_PATH, folder, name)
    mask_full_path = os.path.join(MASKS_PATH, folder, name)

    # load image from full path
    img = cv2.imread(img_full_path)
    # load mask from full path
    mask = cv2.imread(mask_full_path)

    # get all indexes for which is color white in the mask
    indexes = np.where(mask == 255)
    print(check_mask_connected(indexes))

    # based on indexes, set change color in img to be darker
    img[indexes] = img[indexes] * 0.5

    # visu new image
    cv2.imshow("image", img)
    cv2.waitKey(0)


def find_completely_wrong(to_adjust):
    # find wrongly shaped directories

    probably_wrong_shape = set()
    has_somthing_ok = set()

    for (folder, img) in to_adjust:

        for student_name, _, _ in to_adjust[(folder, img)]:
            if student_name in ignore_list:
                continue

            in_annotations_address_mask = os.path.join(ANNOTATIONS_PATH, student_name, "masks", folder.zfill(3), f"{img.zfill(2)}.png")
            in_large_uploads_address_mask = os.path.join(LARGE_UPLOADS_PATH, student_name, "masks", folder.zfill(3), f"{img.zfill(2)}.png")

            # try to find the mask in either if these, if fail store in probably_wrong_shape
            if os.path.exists(in_annotations_address_mask):
                # mask = cv2.imread(in_annotations_address_mask)
                has_somthing_ok.add(student_name)
            elif os.path.exists(in_large_uploads_address_mask):
                # mask = cv2.imread(in_large_uploads_address_mask)
                has_somthing_ok.add(student_name)
            else:
                probably_wrong_shape.add(student_name)

    for name in probably_wrong_shape:
        if name not in has_somthing_ok:
            print(name)


def get_mask_address(student_name, folder, img):
    in_annotations_address_mask = os.path.join(ANNOTATIONS_PATH, student_name, "masks", folder.zfill(3),
                                               f"{img.zfill(2)}.png")
    in_large_uploads_address_mask = os.path.join(LARGE_UPLOADS_PATH, student_name, "masks", folder.zfill(3),
                                                 f"{img.zfill(2)}.png")

    mask = None
    # try to find the mask in either if these, if fail store in probably_wrong_shape
    # also note that both possible locations are tested
    if os.path.exists(in_annotations_address_mask):
        mask = in_annotations_address_mask
    elif os.path.exists(in_large_uploads_address_mask):
        mask = in_large_uploads_address_mask

    return mask

def get_img_address(student_name, folder, img):
    in_annotations_adress_image = os.path.join(ANNOTATIONS_PATH, student_name, "images", folder.zfill(3),
                                               f"{img.zfill(2)}.png")
    in_large_uploads_adress_image = os.path.join(LARGE_UPLOADS_PATH, student_name, "images", folder.zfill(3),
                                                 f"{img.zfill(2)}.png")

    image_address = None

    if os.path.exists(in_annotations_adress_image):
        image_address = in_annotations_adress_image
    elif os.path.exists(in_large_uploads_adress_image):
        image_address = in_large_uploads_adress_image

    return image_address


def find_masks_to_clear_adjustion(to_adjust):
    # passes content of to_correct and loads the corrected masks and so there can later be an aggregation over them
    # ignores all the cases where the image could have been adjusted though

    adjusted_masks = {}

    for (folder, img) in to_adjust:
        if (folder, img) in adjusted_masks and adjusted_masks[(folder, img)] is None:
            continue

        for student_name, _, s in to_adjust[(folder, img)]:


            mask = get_mask_address(student_name, folder, img)
            image_address = get_img_address(student_name, folder, img)

            # we're looking only for cases, where the image wasn't adjusted
            if mask is not None and image_address is not None:
                adjusted_masks[(folder, img)] = None
                break


            if mask is not None:
            #  means we have a mask to adjust and the image did not change at all
                if (folder, img) not in adjusted_masks:
                    adjusted_masks[(folder, img)] = []

                adjusted_masks[(folder, img)].append(mask)

    # now we have a dictionary, where the key is (folder, img) and the value is a list of masks
    return adjusted_masks


def count_all_images():
    # count all images in IMGS_PATH
    img_count = 0
    for folder in os.listdir(IMGS_PATH):
        for img in os.listdir(os.path.join(IMGS_PATH, folder)):
            if img.endswith(".png"):
                img_count += 1

    print("img_count", img_count)


def aggregate_and_store_masks(mask_adresses):

    def get_mean_mask_index(masks_adresses):
        indexes_to_use = {}

        for key in masks_adresses:
            contents = []

            if masks_adresses[key] is None:
                continue

            for mask_adrr in masks_adresses[key]:
                #load mask
                mask = cv2.imread(mask_adrr)
                indexes = np.where(mask != 0)

                if len(indexes[0]) not in contents:
                    contents.append(len(indexes[0]))

            # get the index of the mask with the mean number of pixels
            if len(contents):
                indexes_to_use[key] = np.argmin(np.abs(np.array(contents) - np.mean(contents)))
            else:
                indexes_to_use[key] = None

        return indexes_to_use


    for img_key in mask_adresses:
        masks = mask_adresses[img_key]
        if masks is None:
            continue
        # load masks
        loaded_masks = []
        # todo check desired shape based on the provided img
        files = ["large uploads", "annotations"]
        for f in files:
            if f in masks[0]:
                splitted = masks[0].split(os.sep)
                folder, file = splitted[-2], splitted[-1]
                img_addr = os.path.join(IMGS_PATH, folder, file)
                break
        # sanity check
        # load images and get shape
        img = cv2.imread(img_addr)
        desired_shape = img.shape

        acceptable_masks = []
        for mask_path in masks:
            loaded_masks.append(cv2.imread(mask_path))
            if loaded_masks[-1].shape != desired_shape:
                print(f"shape mismatch, desired: {desired_shape}, provided: {loaded_masks[-1].shape}", mask_path)
            else:
                acceptable_masks.append(mask_path)

        # fixme shouldnt adjust the item that is being iterated over
        mask_adresses[img_key] = acceptable_masks

    # todo do the aggregations
    agregation_indexes = get_mean_mask_index(mask_adresses)

    res = get_final_img_and_mask(mask_adresses, agregation_indexes)

    print("res", res)



    # todo store based on the key





def get_final_img_and_mask(orig, desired):
    res = {}

    for i, key in enumerate(orig):
        if orig[key] is None:
            continue

        if desired[key] is not None:
            res[key] = orig[key][desired[key]]
        else:
            print("no correct mask found for", key)

    return res


def aggregate_and_store_masks_and_images(masks_and_image_adresses):
    def get_mean_mask_index(masks_and_image_adresses):
        indexes_to_use = {}

        for key in masks_and_image_adresses:
            contents = []

            for mask_adrr, img_adrr in masks_and_image_adresses[key]:
                #load mask
                mask = cv2.imread(mask_adrr)
                indexes = np.where(mask != 0)

                if len(indexes[0]) not in contents:
                    contents.append(len(indexes[0]))

            # get the index of the mask with the mean number of pixels
            indexes_to_use[key] = np.argmin(np.abs(np.array(contents) - np.mean(contents)))
        return indexes_to_use

    mean_indexes = get_mean_mask_index(masks_and_image_adresses["l"])
    final_l = get_final_img_and_mask(masks_and_image_adresses["l"], mean_indexes)

    mean_indexes = get_mean_mask_index(masks_and_image_adresses["r"])
    final_r = get_final_img_and_mask(masks_and_image_adresses["r"], mean_indexes)

    print(final_l)

def get_mask_for_adjusted_image(to_adjust):
    masks_adresess = {
        "l": {},
        "r": {}
    }

    for (folder, img) in to_adjust:
        for i, (student_name, _, _) in enumerate(to_adjust[(folder, img)]):

            # we need new masks for all the adjusted images
            # for each image, store both left and right ears with the paths
            mask_adresess = get_mask_address(student_name, folder, img)
            image_address = get_img_address(student_name, folder, img)

            if mask_adresess is not None and image_address is not None:
                # get annotation

                side = to_adjust[(folder, img)][i][2]
                if (folder, img) not in masks_adresess[side]:
                    masks_adresess[side][(folder, img)] = []

                masks_adresess[side][(folder, img)].append((mask_adresess, image_address))

    return masks_adresess





def check_for_unreported_corrections():

    # get reports

    # get all correctection

    # find if corrections miss a report

    pass



# ____________________________________________________________________________________

def aggregate_and_store_masks_complete():
    to_adjust = get_image_to_adjust()

    masks_addresses = find_masks_to_clear_adjustion(to_adjust)

    # todo store actually
    aggregate_and_store_masks(masks_addresses)



def aggregate_and_store_masks_and_images_complete():
    to_adjust = get_image_to_adjust()

    masks_and_image_adresses = get_mask_for_adjusted_image(to_adjust)

    # todo store actually
    aggregate_and_store_masks_and_images(masks_and_image_adresses)




if __name__ == "__main__":
    # visu_image_and_mask("619", f"08.png")
    to_adjust = get_image_to_adjust()

    # find_completely_wrong(to_adjust)
    # visu_image_and_mask("002", "10.png")

    # to_adjust = get_image_to_adjust()
    # find_completely_wrong(to_adjust)
    #
    # masks_addresses = find_masks_to_clear_adjustion(to_adjust)
    #
    # print("olala")

    # aggregate_and_store_masks_complete()
    aggregate_and_store_masks_complete()

    # aggregate_and_store_masks_and_images_complete()