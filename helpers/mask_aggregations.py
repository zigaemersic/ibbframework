import json
import os
import pickle

import cv2
import numpy as np

from constants import *
from helpers.checking_functions import checkup_missing_mask


def get_image_to_adjust():
    to_correct = {}

    # pass files in annotations folder
    for student_name in os.listdir(ANNOTATIONS_PATH):

        csv_path = os.path.join(ANNOTATIONS_PATH, student_name, f"{student_name}.csv")

        # read csv file

        with open(csv_path, "r") as f:
            data = f.readlines()


        data = data[1:] if not data[0].split(",")[0].isdigit() else data



        for line in data:
            splitted = line.split(";")

            if len(splitted) <= 5 or splitted[5] == "\n" or splitted[5] == "":
                continue

            if len(splitted) == 7:
                folder, img, _, _, s, m, _ = splitted
            else:
                folder, img, _, _, s, m = splitted
                m = m.strip()


            if "/" in img:
                img = img.split("/")[1]

            if len(img) == 3:
                img = img[1:]

            # add leading zero to img so it is 2 digits
            img = img.zfill(2)
            folder.zfill(3)

            if (folder, img) not in to_correct:
                to_correct[(folder, img)] = []
            to_correct[(folder, img)].append((student_name, m, s.strip()))

    # returns a dictionary, where the key is  (folder, img) and the value is a list of tuples (student_name, message)
    return to_correct


def get_images_to_adjust_from_corrected_but_not_anotated():
    with open("copy_pasted_candidates.csv", "r") as f:
        data = f.readlines()

    data = data[1:] if not data[0].split(",")[0].isdigit() else data
    to_correct = {}

    for line in data[1:]:
        student_name, folder, img = line.split(";")


        if (folder, img) not in to_correct:
            to_correct[(folder, img)] = []
        to_correct[(folder, img)].append((student_name, EXPLAIN_MSG_FROM_NOT_ANNOTATED, EXPLAIN_MSG_FROM_NOT_ANNOTATED))

    return to_correct

def get_all_imgs_to_adjust():
    # returns a list of all the images that need to be adjusted
    imgs_to_adjust = get_image_to_adjust()
    imgs_to_adjust.update(get_images_to_adjust_from_corrected_but_not_anotated())

    return imgs_to_adjust


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
    local_mistakes_dict = {}

    for (folder, img) in to_adjust:
        if (folder, img) in adjusted_masks and adjusted_masks[(folder, img)] is None:
            continue

        for student_name, _, s in to_adjust[(folder, img)]:


            mask_address = get_mask_address(student_name, folder, img)
            image_address = get_img_address(student_name, folder, img)

            # check and store wrong situations
            checkup_missing_mask(mask_address, image_address, student_name, local_mistakes_dict)


            # we're looking only for cases, where the image wasn't adjusted
            if mask_address is not None and image_address is not None:
                adjusted_masks[(folder, img)] = None
                break


            if mask_address is not None:
            #  means we have a mask to adjust and the image did not change at all
                if (folder, img) not in adjusted_masks:
                    adjusted_masks[(folder, img)] = []

                adjusted_masks[(folder, img)].append(mask_address)

    # store the mistakes
    # store_mistakes(local_mistakes_dict, "missing masks")


    # now we have a dictionary, where the key is (folder, img) and the value is a list of masks
    return adjusted_masks


def aggregate_and_store_masks(mask_adresses):

    def get_mean_mask_index(masks_adresses):
        indexes_to_use = {}

        cheaters = {}

        for key in masks_adresses:
            contents = []

            by_len = {}

            if masks_adresses[key] is None:
                continue

            for mask_adrr in masks_adresses[key]:
                #load mask
                mask = cv2.imread(mask_adrr)
                indexes = np.where(mask != 0)



                if len(indexes[0]) not in by_len:
                    by_len[len(indexes[0])] = []
                name = mask_adrr.split("/")[-4]
                by_len[len(indexes[0])].append(name)




                if len(indexes[0]) not in contents:
                    contents.append(len(indexes[0]))


            # get the index of the mask with the mean number of pixels
            if len(contents):
                indexes_to_use[key] = np.argmin(np.abs(np.array(contents) - np.mean(contents)))

                # if any of the by_len lists is longer than 1, then we have a cheater
                for k in by_len:
                    if len(by_len[k]) > 1:
                        for name in by_len[k]:

                            if name not in cheaters:
                                cheaters[name] = []
                            cheaters[name].append((key, len(by_len[k]), by_len[k]))

            else:
                indexes_to_use[key] = None

        print("cheaters in mask correction without the image", cheaters)
        # for key in cheaters['dp8949@student.uni-lj.si']:
        #     addr1 = os.path.join(ANNOTATIONS_PATH, "dp8949@student.uni-lj.si", "masks", key[0][0].zfill(3),
        #                                        f"{key[0][1].zfill(2)}.png")
        #     addr2 = os.path.join(ANNOTATIONS_PATH, "bp58607@student.uni-lj.si", "masks", key[0][0].zfill(3),
        #                          f"{key[0][1].zfill(2)}.png")
        #     img1 = cv2.imread(addr1)
        #     img2 = cv2.imread(addr2)
        #     print(img1 == img2)


        return indexes_to_use


    mismatched = {}
    for img_key in mask_adresses:
        masks = mask_adresses[img_key]
        if masks is None:
            continue
        # load masks
        loaded_masks = []
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
                student_name = mask_path.split(os.sep)[-4]
                if student_name not in mismatched:
                    mismatched[student_name] = 0
                mismatched[student_name] += 1
            else:
                acceptable_masks.append(mask_path)

        # fixme shouldnt adjust the item that is being iterated over
        mask_adresses[img_key] = acceptable_masks

    agregation_indexes = get_mean_mask_index(mask_adresses)

    res = get_final_img_and_mask(mask_adresses, agregation_indexes)

    print("res", res)

    for (dir, img_n) in res:
        img_addr = res[(dir, img_n)]
        orig_img = cv2.imread(img_addr)

        addr_addr = os.path.join(MASKS_ONLY_AGGREGATED_FROM_ANNOTATIONS_PATH, dir.zfill(3))
        os.makedirs(addr_addr, exist_ok=True)

        new_addr = os.path.join(addr_addr, f"{img_n.zfill(2)}.png")
        cv2.imwrite(new_addr, orig_img)

    # store_mistakes(mismatched, "mask shape mismatch")



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

        cheaters = {}


        for key in masks_and_image_adresses:
            contents = []

            by_len = {}


            for mask_adrr, img_adrr in masks_and_image_adresses[key]:
                #load mask
                mask = cv2.imread(mask_adrr)
                indexes = np.where(mask != 0)


                if len(indexes[0]) not in by_len:
                    by_len[len(indexes[0])] = []
                name = mask_adrr.split("/")[-4]
                by_len[len(indexes[0])].append(name)




                if len(indexes[0]) not in contents:
                    contents.append(len(indexes[0]))


            # get the index of the mask with the mean number of pixels
            indexes_to_use[key] = np.argmin(np.abs(np.array(contents) - np.mean(contents)))

            # if any of the by_len lists is longer than 1, then we have a cheater
            for k in by_len:
                if len(by_len[k]) > 1:
                    for name in by_len[k]:

                        if name not in cheaters:
                            cheaters[name] = []
                        cheaters[name].append((key, len(by_len[k]), by_len[k]))

        print("cheaters in mask correction with the image", cheaters)


        return indexes_to_use

    mean_indexes = get_mean_mask_index(masks_and_image_adresses["l"])
    final_l = get_final_img_and_mask(masks_and_image_adresses["l"], mean_indexes)
    store_mask_and_image(final_l, "l")

    mean_indexes = get_mean_mask_index(masks_and_image_adresses["r"])
    final_r = get_final_img_and_mask(masks_and_image_adresses["r"], mean_indexes)
    store_mask_and_image(final_r, "r")


def store_mask_and_image(to_store, side):
    for (dir, img_n) in to_store:
        orig_mask_addr, orig_img_addr = to_store[(dir, img_n)]
        orig_mask, orig_img = cv2.imread(orig_mask_addr), cv2.imread(orig_img_addr)

        new_mask_addr = os.path.join(MASKS_FROM_MASKS_AND_IMAGES_AGGREGATED_PATH, dir.zfill(3))
        new_img_addr = os.path.join(IMGS_FROM_MASKS_AND_IMAGES_AGGREGATED_PATH, dir.zfill(3))

        os.makedirs(new_mask_addr, exist_ok=True)
        os.makedirs(new_img_addr, exist_ok=True)

        new_mask_addr = os.path.join(new_mask_addr, f"{img_n.zfill(2)}_{side}.png")
        new_img_addr = os.path.join(new_img_addr, f"{img_n.zfill(2)}_{side}.png")

        cv2.imwrite(new_mask_addr, orig_mask)
        cv2.imwrite(new_img_addr, orig_img)

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




# ____________________________________________________________________________________

def aggregate_and_store_masks_complete():
    to_adjust = get_all_imgs_to_adjust()

    masks_addresses = find_masks_to_clear_adjustion(to_adjust)

    aggregate_and_store_masks(masks_addresses)



def aggregate_and_store_masks_and_images_complete():
    to_adjust = get_all_imgs_to_adjust()

    masks_and_image_adresses = get_mask_for_adjusted_image(to_adjust)

    aggregate_and_store_masks_and_images(masks_and_image_adresses)




if __name__ == "__main__":
    # visu_image_and_mask("619", f"08.png")
    # to_adjust = get_all_imgs_to_adjust()

    # find_completely_wrong(to_adjust)
    # visu_image_and_mask("002", "10.png")

    # find_completely_wrong(to_adjust)
    #
    # masks_addresses = find_masks_to_clear_adjustion(to_adjust)
    #
    # print("olala")

    # aggregate_and_store_masks_complete()
    aggregate_and_store_masks_and_images_complete()