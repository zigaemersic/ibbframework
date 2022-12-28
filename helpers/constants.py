import os
import pickle

import cv2

IMGS_PATH = "/home/petrsejvl/ibb_data/images-zips"
MASKS_PATH = "/home/petrsejvl/ibb_data/masks-zips"
ANNOTATIONS_PATH = "/home/petrsejvl/ibb_data/annotations"
LARGE_UPLOADS_PATH = "/home/petrsejvl/ibb_data/large uploads"
ONLY_MASKS_CORRECTION_PATH = "/home/petrsejvl/ibb_data/only_mask_correction"
MASKS_ONLY_AGGREGATED_FROM_ANNOTATIONS_PATH = "/home/petrsejvl/ibb_data/masks_only_aggregated_from_annotations"
MASKS_FROM_MASKS_AND_IMAGES_AGGREGATED_PATH = "/home/petrsejvl/ibb_data/masks_from_masks_and_images_aggregated"
IMGS_FROM_MASKS_AND_IMAGES_AGGREGATED_PATH = "/home/petrsejvl/ibb_data/images_from_masks_and_images_aggregated"
no_corrections_provided = [
    "jp32669@student.uni-lj.si",
    "fd8651@student.uni-lj.si",
    "zh0444@student.uni-lj.si",
    "mm7522@student.uni-lj.si",
    "mc4857@student.uni-lj.si",
    "mb3926@student.uni-lj.si",
    "ls3453@student.uni-lj.si",
    "ms0181@student.uni-lj.si",
    "jv4739@student.uni-lj.si"
    "nv6920@student.uni-lj.si",
    "jb3976@student.uni-lj.si",
]


MISTAKES_REPORT= "mistakes_report"
EXPLAIN_MSG_FROM_NOT_ANNOTATED = "Note that I have this field only to keep the shape. This image was not annotated by the student, but the student provided a mask for it. This is probably a mistake."










def store_mistakes(mistakes, name):
    # load the mistakes, so they can be later only updated
    with open(f"{MISTAKES_REPORT}.pkl", "rb") as f:
        original = pickle.load(f)

    print("original", original)

    # # comment to be clear that you don't override your results unless wnated
    with open(f"{MISTAKES_REPORT}.pkl", "wb") as f:
        for student in mistakes:

            if student not in original:
                original[student] = {}

            original[student][name] = mistakes[student]

        pickle.dump(original, f)


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


if __name__ == "__main__":
    with open(f"{MISTAKES_REPORT}.pkl", "rb") as f:
        original = pickle.load(f)

    print("original", original)