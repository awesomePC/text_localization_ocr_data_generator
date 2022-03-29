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
    dir_base_input_folder = "out/Qatar-Resident id card - front/synth_cards/"

    # out_dataset_name = "Qatar-resident-id-card-front-1000-PPOCRlabel-format"
    # out_dataset_name = "Qatar-resident-id-card-front-1000-icdar2015-format"
    out_dataset_name = "Qatar-resident-id-card-front-10-icdar2015-format"

    out_dataset_folder = f"./out/final_dataset/{out_dataset_name}"
    os.makedirs(out_dataset_folder, exist_ok=True)

    out_dataset_type = "icdar2015" ## PPOCRLabel, icdar2015

    ##
    test_size = 0.10

    if out_dataset_type == "icdar2015":
        out_imgs_folder = os.path.join(out_dataset_folder, "imgs")
        os.makedirs(out_imgs_folder, exist_ok=True)

        out_annonation_folder = os.path.join(out_dataset_folder, "annotations")
        os.makedirs(out_annonation_folder, exist_ok=True)

    ### List annonation files
    raw_annonation_files = list_files(dir_base_input_folder, filter_ext=[".json"])

    ## Split train-test
    train, test = train_test_split(
        raw_annonation_files, 
        test_size=test_size, random_state=42
    )
    train_set, test_set = set(train), set(test)

    # lst_all_files_final_annotations = []
    lst_train_files_final_annotations = []
    lst_test_files_final_annotations = []

    for raw_annonation_file in tqdm(raw_annonation_files):
        with open(raw_annonation_file, encoding="utf-8") as json_file:
            raw_annonation_data = json.load(json_file)

        ##
        raw_line_annotations = raw_annonation_data["line_annotations"]

        lst_final_annotations = []
        for idx, line_annonation in enumerate(raw_line_annotations):
            final_annotations = {}
            final_annotations['transcription'] = line_annonation["text"]

            left_x, top_y, right_x, bottom_y = line_annonation["coordinates"]
            line_coordinates_4points = [
                [left_x, top_y],
                [right_x, top_y],
                [right_x, bottom_y],
                [left_x, bottom_y]
            ]
            final_annotations['points'] = line_coordinates_4points
            final_annotations['difficult'] = False
            lst_final_annotations.append(final_annotations)

        ## image
        raw_annonation_path = Path(raw_annonation_file)
        file_suffix_number = raw_annonation_path.name.split("_")[0]
        input_img_filepath = os.path.join(
            raw_annonation_path.parent, f"{file_suffix_number}.png"
        )

        inp_parent_foldername = os.path.basename(str(raw_annonation_path.parent))
        # os.path.basename(str(raw_annonation_path.parent)).split("_")

        if out_dataset_type == "icdar2015":
            all_gt = []
            for single_annonation in lst_final_annotations:
                # print(f"single_annonation: ", single_annonation)
                transcription = single_annonation["transcription"]
                points = single_annonation["points"]
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
            if raw_annonation_file in train_set:
                training_foldername = "training"
                out_gt_filepath = os.path.join(
                    out_annonation_folder, training_foldername,
                    f"gt_{file_suffix_number}.txt"
                )
                out_img_filepath = os.path.join(
                    out_imgs_folder, training_foldername, out_img_name
                )

            else:
                test_foldername = "test"
                out_gt_filepath = os.path.join(
                    out_annonation_folder, test_foldername,
                    f"gt_{file_suffix_number}.txt"
                )
                out_img_filepath = os.path.join(
                    out_imgs_folder, test_foldername, out_img_name
                )

            os.makedirs(os.path.dirname(out_gt_filepath), exist_ok=True)
            os.makedirs(os.path.dirname(out_img_filepath), exist_ok=True)

            with open(out_gt_filepath, 'w', encoding="utf-8") as file:
                file.write('\n'.join(all_gt))

            shutil.copy2(input_img_filepath, out_img_filepath)
        else:
            ## default PPOCRLabel format
            out_img_name = f"{file_suffix_number}.png"
            out_img_filepath = os.path.join(out_dataset_folder, out_img_name)
            shutil.copy2(input_img_filepath, out_img_filepath)

            # shutil.copy2(raw_annonation_file, out_raw_annonation_file) ## Copy raw json -- optional

            data = {
                "filename": f"{out_dataset_name}/{out_img_name}",
                "annonation": lst_final_annotations
            }
            if raw_annonation_file in train_set:
                lst_train_files_final_annotations.append(data)
            else:
                lst_test_files_final_annotations.append(data)

    if out_dataset_type == "PPOCRLabel":
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