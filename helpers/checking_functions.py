from PIL import Image

from constants import *
import os



def check_only_masks_in_dir():
    # to_check = [
    #             "jm85537@student.uni-lj.si",
    #             # "it8816@student.uni-lj.si"
    # ]

    to_check = os.listdir(ANNOTATIONS_PATH)
    to_check.extend(os.listdir(LARGE_UPLOADS_PATH))

    good_colors = 0
    wrong_colors = 0

    colors_present = set()

    for user in to_check:
        # check directory
        user_dir = os.path.join(ANNOTATIONS_PATH, user, "masks")

        if not os.path.exists(user_dir):
            user_dir = os.path.join(LARGE_UPLOADS_PATH, user, "masks")

        if not os.path.exists(user_dir):
            print(f"User {user} has no masks")
            continue

        # pass all directiories
        tmp_good_colors = 0
        tmp_wrong_colors = 0
        for dir in os.listdir(user_dir):
            dir_path = os.path.join(user_dir, dir)
            if not os.path.isdir(dir_path):
                continue
            # for all the files in the directory, load them as image and check if only black and white
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if not os.path.isfile(file_path):
                    continue
                try:
                    im = Image.open(file_path)
                except:
                    continue
                im = im.convert("L")

                colors = im.getcolors(im.size[0] * im.size[1])

                colors_without_count = [color[1] for color in colors]
                # Check if the image consists only of black and white colors
                if len(colors) == 2 and (0 in colors_without_count and 255 in colors_without_count):
                    # print("The image consists only of black and white colors.")
                    tmp_good_colors += 1
                else:
                    # print("The image does not consist only of black and white colors.", len(colors))
                    # print(file_path)
                    min_c = min(colors_without_count)
                    max_c = max(colors_without_count)

                    threshold = (max_c + min_c) / 2
                    # pass the image, for each pixel, if the color is not black or white, check if it is close to black or white
                    for x in range(im.size[0]):
                        for y in range(im.size[1]):
                            if im.getpixel((x, y)) != 0 and im.getpixel((x, y)) != 255:
                                if im.getpixel((x, y)) < threshold:
                                    im.putpixel((x, y), 0)
                                else:
                                    im.putpixel((x, y), 255)
                    # save the image
                    print(file_path)
                    im.save(file_path)
                    tmp_wrong_colors += 1

        good_colors += tmp_good_colors
        wrong_colors += tmp_wrong_colors

        print("User: " + user + " has " + str(tmp_good_colors) + " good colors and " + str(tmp_wrong_colors) + " wrong colors.")
    print("Good colors: ", good_colors)
    print("Wrong colors: ", wrong_colors)

    print(2 in colors_present)




def find_completely_wrong(to_adjust):
    # find wrongly shaped directories

    probably_wrong_shape = set()
    has_somthing_ok = set()

    for (folder, img) in to_adjust:

        for student_name, _, _ in to_adjust[(folder, img)]:
            if student_name in no_corrections_provided:
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

def count_all_images():
    # count all images in IMGS_PATH
    img_count = 0
    for folder in os.listdir(IMGS_PATH):
        for img in os.listdir(os.path.join(IMGS_PATH, folder)):
            if img.endswith(".png"):
                img_count += 1

    print("img_count", img_count)





def checkup_missing_mask(mask_address, image_address, student_name, local_mistakes_dict):

    def update_mistakes_dict(mistake_type):
        if student_name not in local_mistakes_dict:
            local_mistakes_dict[student_name] = {}

        if mistake_type not in local_mistakes_dict[student_name]:
            local_mistakes_dict[student_name][mistake_type] = 0

        local_mistakes_dict[student_name][mistake_type] += 1

    if mask_address is None and image_address is None:
        update_mistakes_dict("No mask")
    elif mask_address is None and image_address is not None:
        update_mistakes_dict("No mask, but image provided")



def check_copy_paste_from_assingment(copy_pasted_candidates):
    from helpers.mask_aggregations import get_mask_address

    #some provided way too many corrections, we need want to know if they just wrongly copied the assignment

    copy_pasted = {}

    for  (dir, img_b), student_name in copy_pasted_candidates:
        adjusted_mask_address = get_mask_address(student_name, dir, img_b)
        if adjusted_mask_address is None:
            raise ("Should have never happen lol")
        adjusted_mask = cv2.imread(adjusted_mask_address)


        original_mask_address = os.path.join(MASKS_PATH, dir.zfill(3), f"{img_b.zfill(2)}.png")
        original_mask = cv2.imread(original_mask_address)

        # todo compare the two masks
        # if they are the same, add to copy_pasted
        cmp = adjusted_mask == original_mask

        # check if cmp is a boolean type


        cmp = cmp if type(cmp) == bool else cmp.all()

        if cmp:
            if student_name not in copy_pasted:
                copy_pasted[student_name] = []
            copy_pasted[student_name].append((dir, img_b, adjusted_mask_address))

    # for all the copypasted, delete them
    for student_name in copy_pasted:
        for (dir, img_b, adjusted_mask_address) in copy_pasted[student_name]:
            os.remove(adjusted_mask_address)
            print("Removed", adjusted_mask_address)




def copy_pasted_candidates_to_csv(copy_pasted_candidates):
    # save the copy pasted candidates to csv
    with open("copy_pasted_candidates.csv", "w") as f:
        f.write("student_name;dir;img_b\n")
        for (dir, img_b), student_name in copy_pasted_candidates:
            f.write(f"{student_name};{dir};{img_b}\n")







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







