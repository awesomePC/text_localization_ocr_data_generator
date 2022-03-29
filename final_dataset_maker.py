import os
import json
import shutil
from pathlib import Path
from nb_utils.file_dir_handling import list_files
import csv
import pandas as pd

def main():
    dir_base_input_folder = "out/Qatar-Resident id card - front/synth_imgs/"

    out_dataset_name = "Qatar-resident-id-card-front-50"
    out_folder = f"./out/final_dataset/{out_dataset_name}"
    os.makedirs(out_folder, exist_ok=True)

    ### List annonation files
    raw_annonation_files = list_files(dir_base_input_folder, filter_ext=[".json"])

    lst_all_files_final_annonations = []
    for raw_annonation_file in raw_annonation_files:
        with open(raw_annonation_file, encoding="utf-8") as json_file:
            raw_annonation_data = json.load(json_file)

        ##
        raw_line_annonations = raw_annonation_data["line_annonations"]

        lst_final_annonations = []
        for idx, line_annonation in enumerate(raw_line_annonations):
            final_annonations = {}
            final_annonations['transcription'] = line_annonation["text"]

            left_x, top_y, right_x, bottom_y = line_annonation["coordinates"]
            line_coordinates_4points = [
                [left_x, top_y],
                [right_x, top_y]
                [right_x, bottom_y],
                [left_x, bottom_y]
            ]
            final_annonations['points'] = line_coordinates_4points
            final_annonations['difficult'] = False
            lst_final_annonations.append(final_annonations)

        ## image
        raw_annonation_path = Path(raw_annonation_file)
        input_img_filepath = os.path.join(raw_annonation_path.parent, "result_rendered.png")

        inp_parent_foldername = os.path.basename(str(raw_annonation_path.parent))
        # os.path.basename(str(raw_annonation_path.parent)).split("_")

        out_img_name = f"{inp_parent_foldername}.png"
        out_img_filepath = os.path.join(out_folder, out_img_name)
        shutil.copy2(input_img_filepath, out_img_filepath)

        # shutil.copy2(raw_annonation_file, out_raw_annonation_file) ## Copy raw json -- optional

        lst_all_files_final_annonations.append({
            "filename": f"{out_dataset_name}/{out_img_name}",
            "annonation": lst_final_annonations
        })

    # # import ipdb; ipdb.set_trace()
    ## Write final annonations
    df = pd.DataFrame(lst_all_files_final_annonations)
    print(f"df.info(): ", df.info())
    out_final_csv_path = os.path.join(out_folder, "Label.txt")
    df.to_csv(out_final_csv_path, sep="\t", index=False, header=None, quoting=csv.QUOTE_NONE)
    ## write copy in root folder
    df.to_csv(
        os.path.join(os.path.dirname(out_folder), "Label.txt"),
        sep="\t", index=False, header=None
    )
    print(f"Final label file written to {out_final_csv_path} and in it's parent folder..")
    pass

if __name__ == "__main__":
    main()