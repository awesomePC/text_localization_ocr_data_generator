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
from margin_utils import margins_arg_parse, expand_box
from visualization import draw_boxes

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
        "-m",
        "--margins",
        type=margins_arg_parse,
        nargs="?",
        help="Define the margins around the main box for cropping. In pixels, If single value then 4 times it will be repeated",
        default=(0, 0, 0, 0),
    )

    # , nargs='+', type=int
    # parse the arguments
    args = parser.parse_args()

    dir_base_input_folder = args.base_input_folder

    margins = args.margins

    ### List annotation files
    raw_annotation_files = list_files(dir_base_input_folder, filter_ext=[".json"])

    ## Iterate in final annotations
    for raw_annotation_file in tqdm(raw_annotation_files):
        with open(raw_annotation_file, encoding="utf-8") as json_file:
            raw_annotation_data = json.load(json_file)

        ## If original boxes already modified by previous box expand -- then first restore it
        if (raw_annotation_data.get("is_boxes_expanded")):
            ## remove keys and data
            raw_annotation_data.pop("line_annotations")
            raw_annotation_data.pop("word_annotations")
            ## rename keys
            raw_annotation_data["line_annotations"] = raw_annotation_data.pop("original_line_annotations")
            raw_annotation_data["word_annotations"] = raw_annotation_data.pop("original_word_annotations")
            raw_annotation_data.pop("is_boxes_expanded")

        new_annotation_data = {}
        previous_annotation_data = {}
        for key, item in raw_annotation_data.items():
            if key not in ["word_annotations", "line_annotations"]:
                continue
            
            ## save previous data copy -- to merge this dict later
            previous_annotation_data[f"original_{key}"] = item
            
            ## if valid annotation key
            raw_annotations = item
    
            lst_final_annotations = []
            for idx, annotation in enumerate(raw_annotations):
                final_annotations = {}
                final_annotations['transcription'] = annotation["text"]

                # import pdb; pdb.set_trace()

                if isinstance(annotation["coordinates"][0], list):
                    ## If already 4 points minimal rectangle
                    coordinates_4points = annotation["coordinates"]
                else:
                    ## If rectangle values -- 4 integer values only
                    left_x, top_y, right_x, bottom_y = annotation["coordinates"]

                    coordinates_4points = [
                        [left_x, top_y],
                        [right_x, top_y],
                        [right_x, bottom_y],
                        [left_x, bottom_y]
                    ]
                
                ## make int values
                coordinates_4points = np.asarray(coordinates_4points).astype("int").tolist()

                if margins[0]:
                    ## add margin around it
                    margin_top, margin_left, margin_bottom, margin_right = margins

                    coordinates_4points = expand_box(
                        coordinates_4points,
                        margin_top, margin_left, margin_bottom, margin_right
                    )

                final_annotations['coordinates'] = coordinates_4points
                lst_final_annotations.append(final_annotations)

            ## append modified data in dict
            new_annotation_data[key] = lst_final_annotations

        ## image
        raw_annotation_path = Path(raw_annotation_file)
        file_suffix_number = raw_annotation_path.name.split("_")[0]
        input_img_filepath = os.path.join(
            raw_annotation_path.parent, f"{file_suffix_number}.png"
        )

        base_parent_folder = os.path.dirname(str(raw_annotation_path.parent))

        ## read image
        img_pil = Image.open(input_img_filepath)

        for key in ['line_annotations', 'word_annotations']:
            bounds = [value["coordinates"] for value in new_annotation_data[key]]
            # import  pdb;pdb.set_trace()

            img_pil_2_draw = img_pil.copy()
            # this function call the visualize method to draw the boxes around text
            draw_boxes(
                img_pil_2_draw, bounds=bounds, color='lime', width=1, 
                text_font_size=14, text_fill_color="orange", draw_text_idx=True
            )
            # display(img_pil_2_draw)
            
            visualized_out_dir = os.path.join(
                base_parent_folder, "visualized_expanded_boxes", key
            )
            os.makedirs(visualized_out_dir, exist_ok=True)
            # print(f"visualized_out_dir: ", visualized_out_dir)

            img_pil_2_draw.save(
                os.path.join(
                    visualized_out_dir, f"{file_suffix_number}_visualized.png"
                )
            )

        ## save annotation back to json files
        new_annotation_data["is_boxes_expanded"] = True
        new_annotation_data["margins"] = margins

        ## append original data with modified key such as original_word_annotations
        new_annotation_data.update(previous_annotation_data)
        ## finally overwrite json file
        out_filepath = raw_annotation_file ## same input file as we are overwriting
        with open(out_filepath, "w", encoding="utf-8") as outfile:
            json.dump(new_annotation_data, outfile, indent=4, ensure_ascii=False)
    

    pass

if __name__ == "__main__":
    main()