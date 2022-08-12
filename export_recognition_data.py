"""
Recognition dataset export
"""
import os
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
from sklearn.model_selection import train_test_split
from image_cropping import crop_img_boxes
import cv2
from PIL import Image

def main():
    import argparse

    # create the argument parser
    parser = argparse.ArgumentParser()
    # add an argument
    parser.add_argument(
        "-i", "--base_input_folder", type=str, required=True,
        help="Base input folder to read generated cards data ex. `out/Qatar-Resident id card - front/synth_cards/`"
    )
    parser.add_argument(
        "-o", "--output_folder", type=str, required=True,
        help="Base output folder to save final dataset ex. `./out/final_dataset/Qatar-resident-id-card-front-10-recognition-dataset-line-level`"
    )
    parser.add_argument(
        "-t", "--annotation_type", type=str, required=False,
        default="line",
        help="Annotation type to convert either line or word . Default line"
    )
    parser.add_argument(
        "-p", "--test_dataset_ratio", type=float, required=False,
        default=0.10,
        help="Test dataset percentage 0 to max 1. Default 0.1 means 10% of whole data"
    )
    # parse the arguments
    args = parser.parse_args()

    dir_base_input_folder = args.base_input_folder
    out_dataset_folder = args.output_folder

    out_dataset_name = os.path.basename(out_dataset_folder)
    os.makedirs(out_dataset_folder, exist_ok=True)
    
    annotation_type = args. annotation_type ## either line or word

    ##
    test_size = args.test_dataset_ratio # 0.10

    ### List annotation files
    raw_annotation_files = list_files(dir_base_input_folder, filter_ext=[".json"])

    ## Split train-test
    train, test = train_test_split(
        raw_annotation_files, 
        test_size=test_size, random_state=42
    )
    train_set, test_set = set(train), set(test)

    ## Iterate in final annotations
    train_gt = []
    test_gt = []
    for raw_annotation_file in tqdm(raw_annotation_files):
        with open(raw_annotation_file, encoding="utf-8") as json_file:
            raw_annotation_data = json.load(json_file)

        ##
        if annotation_type == "line":
            raw_annotations = raw_annotation_data["line_annotations"]
        else:
            raw_annotations = raw_annotation_data["word_annotations"]

        lst_final_annotations = []
        for idx, annotation in enumerate(raw_annotations):
            final_annotations = {}
            final_annotations['transcription'] = annotation["text"]

            # import pdb; pdb.set_trace()

            if isinstance(annotation["coordinates"][0], list):
                ## If already 4 points minimal rectangle
                line_coordinates_4points = annotation["coordinates"]
            else:
                ## If rectangle values -- 4 integer values only
                left_x, top_y, right_x, bottom_y = annotation["coordinates"]

                line_coordinates_4points = [
                    [left_x, top_y],
                    [right_x, top_y],
                    [right_x, bottom_y],
                    [left_x, bottom_y]
                ]
            
            ## make int values
            line_coordinates_4points = np.asarray(line_coordinates_4points).astype("int").tolist()

            final_annotations['points'] = line_coordinates_4points
            final_annotations['difficult'] = False
            lst_final_annotations.append(final_annotations)

        ## image
        raw_annotation_path = Path(raw_annotation_file)
        file_suffix_number = raw_annotation_path.name.split("_")[0]
        input_img_filepath = os.path.join(
            raw_annotation_path.parent, f"{file_suffix_number}.png"
        )

        inp_parent_foldername = os.path.basename(str(raw_annotation_path.parent))
        # os.path.basename(str(raw_annotation_path.parent)).split("_")

        ## read image
        image = cv2.imread(input_img_filepath)

        # icdar2015 dataset format
        for idx, single_annotation in enumerate(lst_final_annotations):
            # print(f"single_annotation: ", single_annotation)
            transcription = single_annotation["transcription"]
            points = single_annotation["points"]
            # print(f"points:", points)

            img_crop_list, _ = crop_img_boxes(
                image, np.array([points]), 
                use_angle_cls=False, use_four_point_transform=True
            )
            
            img_cropped_part = img_crop_list[0]

            ## Write gt file and image to disk
            out_img_name = f"{file_suffix_number}_{idx}.jpg"
            if raw_annotation_file in train_set:
                training_foldername = "training"
                out_gt_filepath = os.path.join(
                    out_dataset_folder, training_foldername,
                    f"{file_suffix_number}_{idx}_gt.txt"
                )
                out_img_filepath = os.path.join(
                    out_dataset_folder, training_foldername, out_img_name
                )
                relative_path = Path(out_img_filepath).relative_to(
                    os.path.dirname(out_dataset_folder)
                )
                train_gt.append({
                    "filepath": relative_path,
                    "transcription": transcription
                })
            else:
                test_foldername = "test"
                out_gt_filepath = os.path.join(
                    out_dataset_folder, test_foldername,
                    f"{file_suffix_number}_{idx}_gt.txt"
                )
                out_img_filepath = os.path.join(
                    out_dataset_folder, test_foldername, out_img_name
                )
                relative_path = Path(out_img_filepath).relative_to(
                    os.path.dirname(out_dataset_folder)
                )
                test_gt.append({
                    "filepath": relative_path,
                    "transcription": transcription
                })

            os.makedirs(os.path.dirname(out_gt_filepath), exist_ok=True)
            os.makedirs(os.path.dirname(out_img_filepath), exist_ok=True)
            
            ## Save ground-truth
            with open(out_gt_filepath, 'w', encoding="utf-8") as file:
                file.write(transcription)

            ## save image
            cv2.imwrite(out_img_filepath, img_cropped_part)

    ## Write final annotations
    df_train = pd.DataFrame(train_gt)
    print(f"df_train.info(): ", df_train.info())
    out_final_csv_path = os.path.join(out_dataset_folder, "train-gt.txt")
    df_train.to_csv(out_final_csv_path, sep="\t", index=False, header=None, quoting=csv.QUOTE_NONE)

    df_test = pd.DataFrame(test_gt)
    print(f"df_test.info(): ", df_test.info())
    out_final_csv_path = os.path.join(out_dataset_folder, "test-gt.txt")
    df_test.to_csv(out_final_csv_path, sep="\t", index=False, header=None, quoting=csv.QUOTE_NONE)

    print(f"\nRecognition data successfully exported to `{out_dataset_folder}`\n")
    pass

if __name__ == "__main__":
    main()