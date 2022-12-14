"""
Annotate ocr training dataset generated using card_generator.py script

#  sample Usage
# python augment_ocr_annotation_images_with_coords.py --base_input_folder "out/Telangna Driving Licence - front--100/synth_cards" --logger_level "DEBUG" --output_base_folder "./out/augmented-data"
## base demo script
https://github.com/Nivratti/custom_ocr_pipeline_uwk_project/blob/main/demo_augment_text_detection_image_coordinates.py
"""

import os, sys
import json
import shutil
from pathlib import Path
from nb_utils.file_dir_handling import list_files
import csv
import pandas as pd
from tqdm.auto import tqdm
from functools import reduce
import operator
import numpy as np

import os
import json

import imgaug as ia
import imgaug.augmenters as iaa
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage
from imgaug.augmentables.polys import Polygon, PolygonsOnImage
from shapely import geometry

import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import gdown
from loguru import logger


def draw_boxes(image, bounds, color='lime', width=2, text_font_size=14, text_fill_color="orange"):
    """
    Draw bounding boxes
    PIL text visualization util
    Args:
        image (pil): PIl image
        bounds (polypoints|rect): Text detection bounding boxes
        color (str, optional): Text highlighting color. Defaults to 'yellow'.
        width (int, optional): Border width. Defaults to 2.
    Returns:
        pil: text highlighted image
    """
    font_file = './fonts/Verdana.ttf'
    if not os.path.exists("./fonts"):
        os.makedirs("fonts", exist_ok=True)
    if not os.path.exists("./fonts/Verdana.ttf"):
        url = 'https://drive.google.com/uc?id=1a4Jyh3bwe6v6Hji1WaGgH-7nwA1YOHXb'
        gdown.download(url, font_file, quiet=False)

    font = ImageFont.truetype(font_file, text_font_size)
    
    draw = ImageDraw.Draw(image)
    for idx, bound in enumerate(bounds):
        # print(bound)
        if len(np.array(bound).shape) == 1: 
            ## rectangle
            xmin, xmax, ymin, ymax = bound
            draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=width)
        else:
            # Polygon
            p0, p1, p2, p3 = bound
            draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width)

            text = f"{idx}"
            draw.text(p0, text, font=font, align ="left", fill=text_fill_color) 
    return image

def np_encoder(object):
    if isinstance(object, (np.generic, np.ndarray)):
        return object.tolist()
        
def augment_ocr_image(
        annotations, image, seq
    ):
    """
    Augment OCR Image with minimal area bounding boxes

    Args:
        annotations (_type_): _description_
        image (_type_): _description_
        seq (_type_): _description_
        is_visualize_4points_boxes (bool, optional): _description_. Defaults to False.
    """
    lst_polys = []

    ## 1. First get line annotations and append in list
    line_annotations = annotations["line_annotations"]
    for idx, line_coords in enumerate(line_annotations):
        first_line_coords = line_annotations[idx]["coordinates"]
        x1, y1, x2, y2 = first_line_coords
        poly = BoundingBox.to_polygon(
            BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
        )
        # print(f"poly: ", poly)
        lst_polys.append(poly)

    ## 2. second get word annotations and append in list
    ## Append in same list we can separate it later after augmentation
    word_annotations = annotations["word_annotations"]
    for idx, word_coords in enumerate(word_annotations):
        first_word_coords = word_annotations[idx]["coordinates"]
        x1, y1, x2, y2 = first_word_coords
        poly = BoundingBox.to_polygon(
            BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
        )
        # print(f"poly: ", poly)
        lst_polys.append(poly)

    # logger.debug(f"lst_polys: {lst_polys}")

    polys = PolygonsOnImage(lst_polys, shape=image.shape)
    logger.debug(f"polys: {polys} \n")

    # Augment polygons and images.
    image_aug, polys_aug = seq(image=image, polygons=polys)

    # print coordinates before/after augmentation (see below)
    # use .x1_int, .y_int, ... to get integer coordinates
    for i in range(len(polys.polygons)):
        logger.debug(f"-" * 50)
        before = polys.polygons[i]
        logger.debug(f"before: {before}")
        after = polys_aug.polygons[i]
        logger.debug(f"after: {after}")

    # Convert new polygons(augmented) to 4 points format
    lst_four_points = []
    for i in range(len(polys_aug.polygons)):
        shapely_poly = polys_aug[i].to_shapely_polygon()
        # print(f"to_shapely_polygon: ", shapely_poly)

        coords = np.array(shapely_poly.exterior.coords)
        four_points = coords[:-1] # remove last point to make it 4

        ## store in list
        lst_four_points.append(four_points)

    # import pdb; pdb.set_trace()
    logger.debug(f"lst_four_points: {lst_four_points}")

    ## check is polys going outside the image
    total_polys_aug = len(polys_aug.polygons)
    outside_polys = []
    for poly in polys_aug.polygons:
        if poly.is_fully_within_image(image.shape):
            pass
        else:
            outside_polys.append(poly)

    if len(outside_polys):
        logger.debug(f"Total {len(outside_polys)} boxes out of {total_polys_aug} are outside the image..")
    else:
        logger.debug(f"All boxes are inside the image..")
    
    if outside_polys:
        is_all_boxes_inside_image = False
    else:
        is_all_boxes_inside_image = True

    ## Split augmented annotations inti again line and words level -- separate it
    aug_line_annotations = lst_four_points[0:(len(line_annotations)-1)]
    aug_word_annotations = lst_four_points[len(line_annotations):]

    ## Save modified annotations
    new_line_annotations = []
    for i, four_points in enumerate(aug_line_annotations):
        new_line_annotations.append(
            {
                "text": line_annotations[i]["text"],
                "coordinates": four_points
            }
        )

    new_word_annotations = []
    for i, word_four_points in enumerate(aug_word_annotations):
        new_word_annotations.append(
            {
                "text": word_annotations[i]["text"],
                "coordinates": word_four_points
            }
        )
        
    new_aug_annotations = {
        "new_line_annotations": new_line_annotations,
        "new_word_annotations": new_word_annotations
    }

    return (image_aug, new_aug_annotations, is_all_boxes_inside_image)

def visualize_save_aug_boxes_img(
    pil_img_aug, lst_four_points, 
    visualized_aug_out_file_path,
    is_visualize_4points_boxes=False,
    save_visualized_augmented_image=True,
    vis_color='lime', vis_width=2,
    vis_text_fill_color="orange"
    ):
    # is_visualize_4points_boxes = True
    if (is_visualize_4points_boxes) or (save_visualized_augmented_image):
        pil_img_aug_visualized = draw_boxes(
            pil_img_aug.copy(), lst_four_points, color=vis_color, width=vis_width, text_font_size=14, 
            text_fill_color=vis_text_fill_color
        )
        
        if is_visualize_4points_boxes:
            pil_img_aug_visualized.show()
            # input(f"Press any key to continue...")

        if (save_visualized_augmented_image):
            # pil_img_aug_visualized.convert("RGB").save("visualized_augmented_boxes.jpg")
            # visualized_aug_out_file_path = os.path.join(output_folder, path_object.name)
            os.makedirs(os.path.dirname(visualized_aug_out_file_path), exist_ok=True)
            pil_img_aug_visualized.save(visualized_aug_out_file_path)


def str2bool(v):
    import argparse
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 'True', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'False', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    import argparse

    # create the argument parser
    parser = argparse.ArgumentParser()
    # add an argument
    parser.add_argument(
        "-i", "--base_input_folder", type=str, required=True,
        help="Base input folder to read annotated data generated by card generator"
    )
    parser.add_argument(
        "-o", "--output_base_folder", type=str, required=True,
        help="Output folder to store augmented images"
    )
    parser.add_argument(
        "-lv", "--logger_level", type=str, required=False, 
        default="INFO", help="Loguru logger level"
    )
    parser.add_argument(
        "-c", "--color_value", type=int, required=False, 
        default=0, help="color value to fill corners after applying affine augmentation"
    )

    parser.add_argument(
        "-v", "--is_visualize_4points_boxes", type=str2bool, nargs='?', const=True, default=False, 
        help="Whether to visualize augmented images and boxes"
    )
    parser.add_argument(
        "-s", "--save_visualized_augmented_image", type=str2bool, nargs='?', const=True, default=True, 
        help="Whether to save augmented images with boxes drawn on it"
    )

    # parse the arguments
    args = parser.parse_args()

    logger_level = args.logger_level
    color_value = args.color_value
    is_visualize_4points_boxes = args.is_visualize_4points_boxes
    save_visualized_augmented_image = args.save_visualized_augmented_image

    # logger config
    logger.remove() # remove previously added handler -- to make a fresh start
    logger.add(
        sys.stdout, colorize=True, 
        format="<green>{time:HH:mm:ss}</green> | {level} | {name} | <level>{message}</level>",
        level=logger_level, enqueue=True, backtrace=True, diagnose=True
    )

    base_input_folder = args.base_input_folder
    if not os.path.exists(base_input_folder):
        sys.exit(f"Base input folder {base_input_folder} not exists on disk")
        
    output_base_folder = args.output_base_folder
    os.makedirs(output_base_folder, exist_ok=True)

    # image_file = "imgs/text_detection_synth_imgs/synth_digital_meter/0000.png"
    # json_annotation_file = "imgs/text_detection_synth_imgs/synth_digital_meter/0000_annotations.json"

    seq = iaa.Sequential([

            # crop some of the images by 0-10% of their height/width
            iaa.Sometimes(0.1, iaa.Crop(percent=(0, 0.1))),

            # Apply affine transformations to some of the images
            # - scale to 80-120% of image height/width (each axis independently)
            # - translate by -20 to +20 relative to height/width (per axis)
            # - rotate by -45 to +45 degrees
            # - shear by -16 to +16 degrees
            # - order: use nearest neighbour or bilinear interpolation (fast)
            # - mode: use any available mode to fill newly created pixels
            #         see API or scikit-image for which modes are available
            # - cval: if the mode is constant, then use a random brightness
            #         for the newly created pixels (e.g. sometimes black,
            #         sometimes white)
            iaa.Sometimes(0.5, 
                iaa.Affine(
                    scale={"x": (0.8, 1.2), "y": (0.8, 1.2)},
                    translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
                    rotate=(-30, 30),
                    shear=(-2, 2),
                    order=[0, 1],
                    # cval=(0, 255),
                    # mode=ia.ALL
                    cval=color_value,
                    mode="constant"
                )
            ),
            #
            # Execute 0 to 5 of the following (less important) augmenters per
            # image. Don't execute all of them, as that would often be way too
            # strong.
            #
            iaa.SomeOf((1, 5),
                [
                    iaa.OneOf([
                        # Blur each image with varying strength using
                        # gaussian blur (sigma between 0 and 3.0),
                        # average/uniform blur (kernel size between 2x2 and 7x7)
                        # median blur (kernel size between 3x3 and 11x11).
                        iaa.Sometimes(0.5,
                            iaa.OneOf([
                                iaa.GaussianBlur((0, 2.0)),
                                iaa.AverageBlur(k=(2, 6)),
                                iaa.MedianBlur(k=(3, 3)), ## more value may disturb text
                                iaa.MotionBlur(k=(3, 5), angle=[-45, 45]) # more kernel size 5 -- text may go outside the tight bounding boxes as per single testing
                            ])
                        ),

                        ## Or jpeg compression
                        iaa.Sometimes(0.5, iaa.JpegCompression(compression=(75, 95)))
                    ]),

                    # Add a value of -10 to 10 to each pixel.
                    iaa.Sometimes(0.5, iaa.Add((-10, 10))),

                    # Change brightness of images (80-140% of original value).
                    iaa.Sometimes(1, iaa.Multiply((0.85, 1.3))),

                    # Improve or worsen the contrast of images.
                    iaa.Sometimes(0.5, iaa.LinearContrast((0.8, 1.2))),

                    # 
                    iaa.Sometimes(0.3, iaa.PerspectiveTransform(scale=(0.0, 0.03))),

                    iaa.Sometimes(0.2, iaa.SaltAndPepper(0.0, 0.005)),

                    iaa.Sometimes(0.5,
                        iaa.OneOf([
                            iaa.AddToHueAndSaturation((-20, 20)),
                            iaa.ChangeColorTemperature((2000, 10000))
                        ])
                    )
                ],
            )

        ], 
        # do all of the above augmentations in random order
        random_order=True
    )
    
    ## expects jpeg 3 color value
    # iaa.Sometimes(0.4, iaa.JpegCompression(compression=(70, 99))),

    img_files = list_files(base_input_folder, filter_ext=[".png", ".jpeg", ".jpg"])

    ## TODO: Add feature to generate more augmentation sample per image
    for index_img, image_file in enumerate(tqdm(img_files)):
        p = Path(image_file)
        pil_img = Image.open(image_file)

        ## To add support for some augmentation such as jpeg_compression, AddToHueAndSaturation
        ## 
        pil_img = pil_img.convert("RGB")

        image = np.asarray(pil_img)

        logger.debug(f"image.shape: {image.shape}")

        json_filename = f"{p.stem}_annotations.json"
        json_annotation_file = p.with_name(json_filename)
        logger.debug(f"json_annotation_file: {json_annotation_file}")

        # read json file get word annotation coordinates
        ## Currently only line augmentations
        ## TODO: Add support for both (line and word level at once) to augment
        ## To this you can combine them in single list and pass to aug -- after that
        ## you can split augmented boxes list based on index and get 
        with open(json_annotation_file) as f:
            annotations = json.load(f)

        logger.debug(f"annotations: {annotations} \n")

        ## Augment ocr annotation image with coordinates
        ## Add in loop incase if boxes goes outside then generate new
        is_all_boxes_inside_image = True
        for k in range(0, 5):
            image_aug, new_aug_annotations, is_all_boxes_inside_image = augment_ocr_image(
                annotations, image, seq
            )
            if (is_all_boxes_inside_image):
                ## If all boxes inside image after applying augmentation then it's valid aug , no need to generate new
                break
            else:
                logger.debug(f"Boxes going outside image after augmentation, re-augmentations image for proper aug")

        pil_img_aug = Image.fromarray(image_aug)

        ## save augmented image
        aug_out_sub_folder = os.path.join(output_base_folder, "augmented_imgs")
        os.makedirs(aug_out_sub_folder, exist_ok=True)
        aug_out_file_path = os.path.join(aug_out_sub_folder, p.name)
        pil_img_aug.save(aug_out_file_path)

        ## --------------------------------------------------------
        ## Write meta in json
        final_meta = {
            "line_annotations": new_aug_annotations["new_line_annotations"],
            "word_annotations": new_aug_annotations["new_word_annotations"],
            "is_augmented_boxes": True
        }
        # import pdb; pdb.set_trace()

        out_filepath = os.path.join(
            aug_out_sub_folder, f"{p.stem}_annotations.json"
        )
        with open(out_filepath, "w", encoding="utf-8") as outfile:
            ## convert numpy to list first
            final_meta = json.loads(json.dumps(final_meta, default=np_encoder))
            json.dump(final_meta, outfile, indent=4, ensure_ascii=False)
    
        ## Visualize line annotations if enabled and save
        line_cords = [e["coordinates"] for e in new_aug_annotations["new_line_annotations"]]
        visualize_save_aug_boxes_img(
            pil_img_aug,
            line_cords,
            visualized_aug_out_file_path=os.path.join(
                output_base_folder, "visualized_box_imgs", "line_level", p.name
            ),
        )
        ## Visualize word level annotations if enabled and save
        word_coords = [e["coordinates"] for e in new_aug_annotations["new_word_annotations"]]
        visualize_save_aug_boxes_img(
            pil_img_aug,
            word_coords,
            visualized_aug_out_file_path=os.path.join(
                output_base_folder, "visualized_box_imgs", "word_level", p.name
            ),
        )

        # if (index_img > 1):
        #     logger.error("Early stopping due to break statement...")
        #     break # for dev only
        

if __name__ == "__main__":
    main()