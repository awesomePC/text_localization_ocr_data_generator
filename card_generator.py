import os,sys
import subprocess
import imutils
from PIL import Image

# importing the module
import json

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
    return img.resize(dim, Image.ANTIALIAS)

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

    ## For dev
    # box_index = 0
    # box = boxes[box_index]
    ## /end dev

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
            word_img = resize_pil_image(word_img, height=box_height)
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

            ## update last_rendered_image_topright_coordinates
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

if __name__ == "__main__":
    main()