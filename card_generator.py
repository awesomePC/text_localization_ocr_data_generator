import os,sys
import subprocess
import imutils
from PIL import Image

# importing the module
import json

from visualization import draw_boxes

parent_folder = os.path.dirname(os.path.abspath(__file__))
submodule_path = os.path.join(parent_folder, "TextRecognitionDataGenerator")
sys.path.append(submodule_path)

py_cmd = [
    "python",
    "TextRecognitionDataGenerator/trdg/run.py",
]

common_cmd_params = [
    "--name_format", "2",
    "--extension", "png",
    "--image_mode", "RGBA",
    "--output_bboxes", "1",
    "--background", "4",
    "--word_split",
    "--fit",
]

def resize_pil_image(img, width=None, height=None):
    """
    Resize PIL image - maintain aspect ratio

    Args:
        img (PIL): Pil image to resize
        width (int, optional): If resize by width. Defaults to None.
        height (int, optional): If resizing by height. Defaults to None.

    Returns:
        PIL: Resized image
    """
    dim = None
    (w, h) = img.size

    if not height and not width:
        print(f"Error ... Either new width or height should be passed..")
        return False

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))
            
    # resize the image
    return (img.resize(dim, Image.ANTIALIAS), r)

def get_points_dims(points):
    """
    Get points height and width dimensions

    Args:
        points (list): List of list -- 4 points format
    """
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
    return (height, width)

def main():
    """
        Description: Main function
    """
    ## ---------------------------------------------------------------------
    # Opening JSON file
    json_meta_file = "./data/document-id-template/UAE-identity-card-front/meta.json"
    with open(json_meta_file) as json_file:
        meta_data = json.load(json_file)
    
    # print(meta_data)

    project_name = meta_data["project_name"]
    base_dir_path = meta_data["base_dir_path"]
    image_path_original = meta_data["image_path"]["original"]
    blank_image_path = meta_data["image_path"]["blank_image"]
    boxes = meta_data["boxes"]

    ## --------------------------------------------------------------------
    base_dir = base_dir_path # "./data/document-id-template/UAE-identity-card-front"
    ## Pasting generated word image
    doc_cleaned_img_file = os.path.join(base_dir, blank_image_path) # "cleaned.png")
    document_bg_img = Image.open(doc_cleaned_img_file).convert("RGBA")

    # ## ----------------------------------------------------------------------
    output_root_dir = os.path.join("out", project_name)
    os.makedirs(output_root_dir, exist_ok=True)

    ## Result coordinates types -- 
    ## 1: 4 points : [[], [], [], []]
    ## 2. Rect : 4 numbers ex.
    final_coordinate_types = "4-points"
    
    ## For dev
    # box_index = 0
    # box = boxes[box_index]
    ## /end dev

    ## List to store all annonations
    line_annonations = [] 
    word_annonations = [] 

    ## Render blocks
    for box_index, box in enumerate(boxes):
        box_type = box["box_type"]
        box_coordinates = box["box_coordinates"]
        alignment = box["alignment"]
        render_text = box["render_text"]
        language = box["lang"]
        is_multi_lang_parts = box["is_multi_lang_parts"]
        margins = box.get("margins", 3)
        box_height, box_width = get_points_dims(points=box_coordinates)

        ## Check is it contains multiple language parts
        total_parts = 0
        if alignment == "left":
            last_rendered_image_topright_coordinates = box_coordinates[0] ##  Used if multiple parts
        else:
            ## From right side
            last_rendered_image_topright_coordinates = box_coordinates[1] ##  Used if multiple parts

        if language == "mix" or is_multi_lang_parts or "parts" in box:
            total_parts = len(box["parts"])
            is_multi_lang_parts = True
        else:
            total_parts = 1
        
        all_parts_word_coordinates = []
        all_parts_text = []
        all_parts_words = []
        for part_index in range(0, total_parts):
            if is_multi_lang_parts:
                part = box["parts"][part_index]
                # get single part attributes
                language = part["lang"]
                font = part["font"]
                dict_file = part["dict_file"]
                dict_path = os.path.join(base_dir, dict_file)

                ###
                height = font["font_size"] # 26
                dest_dir = os.path.join(output_root_dir, "boxes",  f"box_{box_index}", f"part_{part_index}")
                os.makedirs(dest_dir, exist_ok=True)

                font_name = font["name"]
                stroke_width = font["stroke_width"]
            else:
                font = box["font"]
                dict_file = box["dict_file"]
                dict_path = os.path.join(base_dir, dict_file)

                ###
                height = font["font_size"] # 26
                dest_dir = os.path.join(output_root_dir, "boxes", f"box_{box_index}")
                os.makedirs(dest_dir, exist_ok=True)
                box_height, box_width = get_points_dims(points=box_coordinates)

                font_name = font["name"]
                stroke_width = font["stroke_width"]

            if not os.path.exists(dict_path):
                print(f"Error... dict_path {dict_path} not exists on disk ...")

            if language in ["en", "english"]:
                font_parent = "latin"
            elif language in ["ar", "arabic"]:
                font_parent = "ar"

            font_filepath = f"TextRecognitionDataGenerator/trdg/fonts/{font_parent}/{font_name}.ttf"
            if not os.path.exists(font_filepath):
                print(f"Error .. Font filepath: {font_filepath} not exists on disk ..")

            cmd = [
                "--dict", dict_path, # "./data/document-id-template/UAE-identity-card-front/dicts/text-2--الإمارات العربية المتحدة.txt",
                "--language", language, # "ar",
                "--margins", str(margins),
                "--format", str(height),
                "--font", font_filepath, # "TextRecognitionDataGenerator/trdg/fonts/ar/Times-New-Roman.ttf",
                "--output_dir", dest_dir,
                "--stroke_width", str(stroke_width)
            ]

            ## final command
            final_cmd = py_cmd + cmd + common_cmd_params
            print(" ".join(final_cmd))

            result = subprocess.run(final_cmd, shell=True, capture_output=False, text=True, stderr=subprocess.STDOUT)
            # print(result)
            ## ----------------------------------------------------------------------

            word_image_file = os.path.join(dest_dir, f"0.png")
            word_img = Image.open(word_image_file).convert("RGBA")
            word_img, img_resizing_ratio = resize_pil_image(word_img, height=box_height)
            print(f"Resizing ratio: ", img_resizing_ratio)
            width_word_img = word_img.size[0]

            if part_index >= 1:
                if alignment == "left":
                    new_position_x = last_rendered_image_topright_coordinates[0]
                    new_position_y = box_coordinates[0][1]
                else:
                    new_position_x = last_rendered_image_topright_coordinates[0] - width_word_img
                    new_position_y = box_coordinates[0][1]
            else:
                if alignment == "left":
                    new_position_x, new_position_y = box_coordinates[0] # 245, 7
                else:
                    ## Width minus from right
                    new_position_x, new_position_y = (
                        box_coordinates[1][0] - width_word_img,
                        box_coordinates[1][1]
                    )

            ## update last_rendered_image_topright_c
            # coordinates
            if alignment == "left":
                last_rendered_image_topright_coordinates = (
                    (new_position_x + width_word_img), new_position_y
                )
            else:
                ## If right to left rendering -- no need to add width
                last_rendered_image_topright_coordinates = (
                    new_position_x, new_position_y
                )

            ## Paste and save
            document_bg_img.paste(word_img,(new_position_x, new_position_y), mask=word_img)
            out_filepath = os.path.join(output_root_dir, f"result_rendered.png")
            document_bg_img.save(out_filepath)

            all_word_coordinates = []
            ## Bounding boxes
            boxes_file = os.path.join(dest_dir, f"0_boxes.txt")
            with open(boxes_file, encoding="utf-8") as fp:
                Lines = fp.readlines()
                for line in Lines[::2]:
                    line = line.strip().replace('\n','')
                    line_splitted = line.split(" ")
                    x, y, x2, y2 = [int(float(i)) for i in line_splitted]
                    coordinates = [x, y, x2, y2 ]

                    ## As per image resizing change cordinate boxes
                    coordinates = [round(value * img_resizing_ratio) for value in coordinates]

                    ## Add current position of x, y as per image pasting -- to get actual box coordinate
                    coordinates = [
                        coordinates[0] + new_position_x, 
                        coordinates[1] + new_position_y,
                        coordinates[2] + new_position_x, 
                        coordinates[3] + new_position_y,
                    ]

                    # print(f"coordinates: ", coordinates)
                    all_word_coordinates.append(coordinates)

            ## Label file
            label_file = os.path.join(dest_dir, f"labels.txt")
            with open(label_file, encoding="utf-8") as fp:
                Lines = fp.readlines()
                for line in Lines:
                    line = line.strip().replace('\n','')
                    splitted_line = line.split(" ", 1)
                    file_name = splitted_line[0]
                    text = splitted_line[1]
                    words = text.split(" ")
                    # print(f"Label text: ", text)
                    # print(f"words: ", words)

            all_parts_word_coordinates.extend(all_word_coordinates)
            all_parts_words.extend(words)
            all_parts_text.append(text) ## Append string value in list - -to join later
        
        # import ipdb; ipdb.set_trace()
        # print(f"all_parts_word_coordinates: ", all_parts_word_coordinates)
        # get final single line details
        line_coordinates = [
            min([c[0] for c in all_parts_word_coordinates]),
            min([c[1] for c in all_parts_word_coordinates]),
            max([c[2] for c in all_parts_word_coordinates]),
            max([c[3] for c in all_parts_word_coordinates])
        ]
        # print(f"line_coordinates: ", line_coordinates)
        line_text = " ".join(all_parts_text)

        # if final_coordinate_types == "4-points":
        #     ## Change rect coordinates to 4 points format
        #     x1, y1, x2, y2 = line_coordinates
        #     line_coordinates_4points = [
        #         [x1, y1], [x2, y1],
        #         [x1, y2 ], [x2, y2]
        #     ]

        #     ## Also for word coordinates
        #     all_words_coordinates_4points = []
        #     for word_coordinates in all_parts_word_coordinates:
        #         x1, y1, x2, y2 = word_coordinates
        #         all_words_coordinates_4points.append([
        #             [x1, y1], [x2, y1],
        #             [x1, y2 ], [x2, y2]
        #         ]) 

        ## Append all data to annonations
        line_annonations.append({
            "text": line_text,
            "coordinates": line_coordinates
        })

        ## All Word coordinates in one list
        for idx, word_coordinates in enumerate(all_parts_word_coordinates):
            word_annonations.append({
                "text": all_parts_words[idx],
                "coordinates": word_coordinates
            })
        # import ipdb; ipdb.set_trace()

    ## Write meta in json
    final_meta = {
        "line_annonations": line_annonations,
        "word_annonations": word_annonations,
    }
    out_filepath = os.path.join(output_root_dir, "annonations.json")
    with open(out_filepath, "w", encoding="utf-8") as outfile:
        json.dump(final_meta, outfile, indent=4, ensure_ascii=False)
    
    ## Visualization
    img_pil = document_bg_img.copy()
    bounds = []
    for line_annonation in line_annonations:
        line_coordinates = line_annonation["coordinates"]
        x1, y1, x2, y2 = line_coordinates
        bounds.append([x1, x2, y1, y2])

    # this function call the visualize method to draw the boxes around text
    draw_boxes(img_pil, bounds=bounds, color='lime', width=1, text_font_size=14, text_fill_color="orange", draw_text_idx=True)
    # display(img_pil)
    img_pil.save(f"{output_root_dir}/line_annonations_visualized.png")


if __name__ == "__main__":
    main()