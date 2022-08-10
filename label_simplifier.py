"""
Obtain height and width of each box
"""
import os
import shutil
import json
import pandas as pd

def main():

    import argparse

    # create the argument parser
    parser = argparse.ArgumentParser()
    # add an argument
    parser.add_argument(
        "-f", "--label_file", type=str, required=True,
        help="Label file path ex. ./data/document-id-template/Quatar-residency-id-front/Label.txt"
    )
    # parse the arguments
    args = parser.parse_args()

    label_file = args.label_file

    dir_base = os.path.dirname(label_file)

    # dir_base = "./data/document-id-template/UAE-identity-card-front"
    # dir_base = "./data/document-id-template/Quatar-residency-id-front"
    # label_file = os.path.join(dir_base, "Label.txt")



    df = pd.read_csv(label_file, sep='\t', names=["filename", "annonation"], engine='python', error_bad_lines=False) ## paddleocr format

    # print("df.head(): ", df.head())
    # print("df.info(): ", df.info())

    all_files_json = []
    for idx, row in df.iterrows():
        str_single_image_annonations = row["annonation"]
        filename = row["filename"]

        # Converting string to list
        annonations = json.loads(str_single_image_annonations)

        all_gt = []
        for single_annonation in annonations:
            transcription = single_annonation["transcription"]
            points = single_annonation["points"]

            # print(f"transcription: ", transcription)
            # print(f"points: ", points)
            height = max(
                points[3][1] - points[0][1],
                points[2][1] - points[1][1],
            )
            ## by x point difference
            width = max(
                points[1][0] - points[0][0],
                points[2][0] - points[3][0],
            )
            # print(f"height: ", height)
            # print(f"width: ", width)

            all_gt.append({
                "transcription": transcription,
                "points": points,
                "height": height,
                "width": width,
            })

        all_files_json.append({
            "filename": filename,
            "all_gt": all_gt
        })

    # print(f"all_files_json: ", all_files_json)
    out_filepath = os.path.join(dir_base, "Label-simplified.json")
    with open(out_filepath, "w", encoding="utf-8") as outfile:
        json.dump(all_files_json, outfile, indent=4, ensure_ascii=False)

    print(f"Simplified label file stored in : {out_filepath}")

if __name__ == "__main__":
    main()