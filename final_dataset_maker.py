"""
Final training dataset format generator -- takes exported cards labels as input
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
        help="Base output folder to save final dataset ex. `./out/final_dataset/Qatar-resident-id-card-front-10-icdar2015-format`"
    )
    parser.add_argument(
        "-t", "--annotation_type", type=str, required=False,
        default="line",
        help="Annotation type to convert either line or word . Default line"
    )
    parser.add_argument(
        "-d", "--det_out_dataset_format", type=str, required=False,
        default="icdar2015",
        help="Dataset type either PPOCRLabel, icdar2015. Default: icdar2015"
    )
    parser.add_argument(
        "-p", "--test_dataset_ratio", type=float, required=False,
        default=0.10,
        help="Test dataset percentage 0 to max 1. Default 0.1 means 10% of whole data"
    )
    # parse the arguments
    args = parser.parse_args()

    # dir_base_input_folder = "out/Qatar-Resident id card - front/synth_cards/"

    # out_dataset_name = "Qatar-resident-id-card-front-1000-PPOCRlabel-format"
    # out_dataset_name = "Qatar-resident-id-card-front-1000-icdar2015-format"
    # out_dataset_name = "Qatar-resident-id-card-front-10-icdar2015-format"
    dir_base_input_folder = args.base_input_folder
    out_dataset_folder = args.output_folder

    out_dataset_name = os.path.basename(out_dataset_folder)
    os.makedirs(out_dataset_folder, exist_ok=True)

    det_out_dataset_format = args.det_out_dataset_format # "icdar2015" ## PPOCRLabel, icdar2015
    annotation_type = args. annotation_type ## either line or word

    ##
    test_size = args.test_dataset_ratio # 0.10

    if det_out_dataset_format == "icdar2015":
        out_imgs_folder = os.path.join(out_dataset_folder, "imgs")
        os.makedirs(out_imgs_folder, exist_ok=True)

        out_annotation_folder = os.path.join(out_dataset_folder, "annotations")
        os.makedirs(out_annotation_folder, exist_ok=True)
        # import ipdb;ipdb.set_trace()

    ### List annotation files
    raw_annotation_files = list_files(dir_base_input_folder, filter_ext=[".json"])

    ## Split train-test
    train, test = train_test_split(
        raw_annotation_files, 
        test_size=test_size, random_state=42
    )
    train_set, test_set = set(train), set(test)

    # lst_all_files_final_annotations = []
    lst_train_files_final_annotations = []
    lst_test_files_final_annotations = []

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

        if det_out_dataset_format == "icdar2015":
            all_gt = []
            for single_annotation in lst_final_annotations:
                # print(f"single_annotation: ", single_annotation)
                transcription = single_annotation["transcription"]
                points = single_annotation["points"]
                flatten_points = reduce(operator.concat, points)
                # only_arabic_transcription = regex.sub(r'[^\u0600-\u06FF]', u'', transcription)

                # if only_arabic_transcription:
                #     # print(only_arabic_transcription, flatten_points)
                #     flatten_points.append(only_arabic_transcription)
                # else:
                #     ## Insert 3 times hash to skip from training
                #     flatten_points.append("###")
                
                ## Append word at last -- as per icdar2015 format
                flatten_points.append(transcription)

                str_gt = ",".join([str(f) for f in flatten_points])
                all_gt.append(str_gt)

            ## Write gt file and image to disk
            out_img_name = f"{file_suffix_number}.png"
            if raw_annotation_file in train_set:
                training_foldername = "training"
                out_gt_filepath = os.path.join(
                    out_annotation_folder, training_foldername,
                    f"gt_{file_suffix_number}.txt"
                )
                out_img_filepath = os.path.join(
                    out_imgs_folder, training_foldername, out_img_name
                )

            else:
                test_foldername = "test"
                out_gt_filepath = os.path.join(
                    out_annotation_folder, test_foldername,
                    f"gt_{file_suffix_number}.txt"
                )
                out_img_filepath = os.path.join(
                    out_imgs_folder, test_foldername, out_img_name
                )

            os.makedirs(os.path.dirname(out_gt_filepath), exist_ok=True)
            os.makedirs(os.path.dirname(out_img_filepath), exist_ok=True)
            
            ## Save ground-truth
            with open(out_gt_filepath, 'w', encoding="utf-8") as file:
                file.write('\n'.join(all_gt))

            ## save image
            shutil.copy2(input_img_filepath, out_img_filepath)
        else:
            ## default PPOCRLabel format
            out_img_name = f"{file_suffix_number}.png"
            out_img_filepath = os.path.join(out_dataset_folder, out_img_name)
            shutil.copy2(input_img_filepath, out_img_filepath)

            # shutil.copy2(raw_annotation_file, out_raw_annotation_file) ## Copy raw json -- optional

            data = {
                "filename": f"{out_dataset_name}/{out_img_name}",
                "annotation": lst_final_annotations
            }
            if raw_annotation_file in train_set:
                lst_train_files_final_annotations.append(data)
            else:
                lst_test_files_final_annotations.append(data)

    if det_out_dataset_format == "PPOCRLabel":
        # # import ipdb; ipdb.set_trace()
        ## Write final annotations
        df_train = pd.DataFrame(lst_train_files_final_annotations)
        print(f"df_train.info(): ", df_train.info())
        out_final_csv_path = os.path.join(out_dataset_folder, "Label-train.txt")
        df_train.to_csv(out_final_csv_path, sep="\t", index=False, header=None, quoting=csv.QUOTE_NONE)

        df_test = pd.DataFrame(lst_test_files_final_annotations)
        print(f"df_test.info(): ", df_test.info())
        out_final_csv_path = os.path.join(out_dataset_folder, "Label-test.txt")
        df_test.to_csv(out_final_csv_path, sep="\t", index=False, header=None, quoting=csv.QUOTE_NONE)

        # ## write copy in root folder
        # df.to_csv(
        #     os.path.join(os.path.dirname(out_dataset_folder), "Label.txt"),
        #     sep="\t", index=False, header=None
        # )
        print(f"Final PPOCRLabel format label file written to {out_final_csv_path} and in it's parent folder..")

    pass

if __name__ == "__main__":
    main()