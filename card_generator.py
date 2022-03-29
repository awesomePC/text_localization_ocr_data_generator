import os,sys
import subprocess
import imutils
from PIL import Image
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import process_map, thread_map  # requires tqdm>=4.42.0
from functools import partial

# importing the module
import json

from visualization import draw_boxes

from python_arabic_reshaper import arabic_reshaper
from bidi.algorithm import get_display

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

def unreshape_arabic_text(text_to_be_unreshape):
    """
    Unreshape text - convert text to original form

    Args:
        text_to_be_unreshape (_type_): _description_

    Returns:
        _type_: _description_
    """
    un_reshaped_text = arabic_reshaper.unreshape(
        text_to_be_unreshape
    )
    # print(un_reshaped_text)
    # print(get_display(un_reshaped_text))
    return get_display(un_reshaped_text)


def generate_data_and_cards(
    image_index=0, meta_data={}, 
    total_images_2_generate=1,
    is_generate_text=True, is_render_text_on_card=False,
    thread_count=1,
    ):
    """
    1. Generate card data using text recognition data generator 
    2. Render generated text on card
    """
    project_name = meta_data["project_name"]
    base_dir_path = meta_data["base_dir_path"]
    boxes = meta_data["boxes"]

    ## Input dir -- metadata, main_img etc
    base_dir = base_dir_path # "./data/document-id-template/UAE-identity-card-front"

    # ## ----------------------------------------------------------------------
    generated_data_root_dir = os.path.join("out", project_name, f"synth_imgs_data")
    os.makedirs(generated_data_root_dir, exist_ok=True)

    ## Main config for rendering card
    ## List to store all annotations
    line_annotations = [] 
    word_annotations = [] 

    image_path_original = meta_data["image_path"]["original"]
    blank_image_path = meta_data["image_path"]["blank_image"]

    ## Card image as a background
    doc_cleaned_img_file = os.path.join(base_dir, blank_image_path) # "cleaned.png")
    document_bg_img = Image.open(doc_cleaned_img_file).convert("RGBA")

    out_dir_cards = os.path.join("out", project_name, f"synth_cards")
    os.makedirs(out_dir_cards, exist_ok=True)
    ## end--Main config for rendering card

    ## Render blocks
    for box_index, box in enumerate(boxes):
        ## if development_mode:
        # if box_index >= 2:
        #     break ## for dev purpose only

        box_type = box["box_type"]
        render_text = box["render_text"]
        box_coordinates = box["box_coordinates"]
        alignment = box["alignment"]
        
        language = box["lang"]
        is_multi_lang_parts = box["is_multi_lang_parts"]
        margins = box.get("margins", 3)

        if language == "mix" or is_multi_lang_parts or "parts" in box:
            total_parts = len(box["parts"])
            is_multi_lang_parts = True
        else:
            total_parts = 1

        if is_render_text_on_card:
            all_parts_word_coordinates = []
            all_parts_text = []
            all_parts_words = []

            ## Alignment
            if alignment == "left":
                last_rendered_image_topright_coordinates = box_coordinates[0] ##  Used if multiple parts
            else:
                ## From right side
                last_rendered_image_topright_coordinates = box_coordinates[1] ##  Used if multiple parts

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
                text_color = font.get("text_color", "#000000,#282828")
                dest_dir = os.path.join(
                    generated_data_root_dir, "boxes", 
                    f"box_{box_index}", f"part_{part_index}"
                )
                os.makedirs(dest_dir, exist_ok=True)

                font_name = font["name"]
                stroke_width = font["stroke_width"]
            else:
                font = box["font"]
                dict_file = box["dict_file"]
                dict_path = os.path.join(base_dir, dict_file)

                ## select specific value from -- multiple values
                dict_file_multiple_values = box.get("dict_file_multi", None)

                ###
                height = font["font_size"] # 26
                # text_color = font.get("text_color", "#000000,#808080") ## diffrent colors
                text_color = font.get("text_color", "#000000,#282828") ## only black

                dest_dir = os.path.join(
                    generated_data_root_dir, "boxes", f"box_{box_index}"
                )
                os.makedirs(dest_dir, exist_ok=True)
                # box_height, box_width = get_points_dims(points=box_coordinates)

                font_name = font["name"]
                stroke_width = font["stroke_width"]

            # print(f"dest_dir: ", dest_dir)
            
            if is_generate_text:
                if not os.path.exists(dict_path):
                    print(f"Error... dict_path {dict_path} not exists on disk ...")

                ### ----------------------------------
                if dict_file_multiple_values:
                    ## multiple values
                    dict_file_multiple_values = box.get("dict_file_multi", None)
                    dict_file_multiple_values_path = os.path.join(base_dir, dict_file_multiple_values)

                    ## new
                    dict_path = dict_file_multiple_values_path
                ## -------------------------------------
                    
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
                    "--text_color", text_color,
                    "--stroke_width", str(stroke_width),
                    "--output_dir", dest_dir,
                    "--count", str(total_images_2_generate),
                    "--thread_count", str(thread_count)
                ]

                ## final command
                final_cmd = py_cmd + cmd + common_cmd_params
                print(" ".join(final_cmd))

                result = subprocess.run(
                    final_cmd, shell=True, capture_output=False,
                    text=True, stderr=subprocess.STDOUT
                )
                # print(result)
                ## ----------------------------------------------------------------------

            if is_render_text_on_card:
                box_height, box_width = get_points_dims(points=box_coordinates)

                ## Check is it contains multiple language parts
                total_parts = 0
                if alignment == "left":
                    last_rendered_image_topright_coordinates = box_coordinates[0] ##  Used if multiple parts
                else:
                    ## From right side
                    last_rendered_image_topright_coordinates = box_coordinates[1] ##  Used if multiple parts

                word_image_file = os.path.join(dest_dir, f"{image_index}.png")
                word_img = Image.open(word_image_file).convert("RGBA")
                word_img, img_resizing_ratio = resize_pil_image(word_img, height=box_height)
                # print(f"Resizing ratio: ", img_resizing_ratio)
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
                # out_card_filepath = os.path.join(
                #     out_dir_cards, f"{image_index:04}.png"
                # )
                # document_bg_img.save(out_card_filepath) ## TODO: save at end

                all_word_coordinates = []
                ## Bounding boxes
                boxes_file = os.path.join(dest_dir, f"{image_index}_boxes.txt")
                with open(boxes_file, encoding="utf-8") as fp:
                    Lines = fp.readlines()
                    for line in Lines[::2]:
                        line = line.strip().replace('\n','')
                        line_splitted = line.split(" ")
                        x, y, x2, y2 = [int(float(i)) for i in line_splitted]
                        coordinates = [x, y, x2, y2 ]

                        ## As per image resizing change cordinate boxes
                        coordinates = [round(value * img_resizing_ratio) for value in coordinates]

                        # ## Increase margin around by some factor
                        # margin_scale_fcator = 0.08
                        # margin_scale_value = round((coordinates[3] - coordinates[1]) * margin_scale_fcator) # margin scale value
                        margin_scale_value = 1 ## Fixed by 2 px
                        # import ipdb; ipdb.set_trace()

                        ## Add current position of x, y as per image pasting -- to get actual box coordinate
                        coordinates = [
                            coordinates[0] + new_position_x - margin_scale_value, 
                            coordinates[1] + new_position_y - margin_scale_value,
                            coordinates[2] + new_position_x + margin_scale_value, 
                            coordinates[3] + new_position_y + margin_scale_value,
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

        if is_render_text_on_card:
            ## Outside parts loop
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

            #     ## Append all data to annotations
            #     """
            #     TODO: Fix error in: unreshape_arabic_text(line_text)
            #     Traceback (most recent call last):
            #     File "card_generator.py", line 424, in <module>
            #         main()
            #     File "card_generator.py", line 386, in main
            #         "text": unreshape_arabic_text(line_text),
            #     File "card_generator.py", line 102, in unreshape_arabic_text
            #         text_to_be_unreshape
            #     File "E:\python\projects\text-localization-ocr-data-generator\python_arabic_reshaper\arabic_reshaper\arabic_reshaper.py", line 318, in unreshape
            #         next_next_char = text_list[index+2]
            #     IndexError: list index out of range
            #     """
            line_annotations.append({
                "text": line_text,
                # "text": unreshape_arabic_text(line_text),
                "coordinates": line_coordinates
            })
            ## All Word coordinates in one list
            for idx, word_coordinates in enumerate(all_parts_word_coordinates):
                word_annotations.append({
                    "text": all_parts_words[idx],
                    # "text": unreshape_arabic_text(all_parts_words[idx]),
                    "coordinates": word_coordinates
                })

    ## Save final data -- after all boxes rendering
    if is_render_text_on_card:
        ## --------------------------------------------------------
        ## Save final card image after rendering all
        out_card_filepath = os.path.join(
            out_dir_cards, f"{image_index:04}.png"
        )
        document_bg_img.save(out_card_filepath)

        ## --------------------------------------------------------
        ## Write meta in json
        final_meta = {
            "line_annotations": line_annotations,
            "word_annotations": word_annotations,
        }
        out_filepath = os.path.join(
            out_dir_cards, f"{image_index:04}_annotations.json"
        )
        with open(out_filepath, "w", encoding="utf-8") as outfile:
            json.dump(final_meta, outfile, indent=4, ensure_ascii=False)
    
        ## Visualization
        # base_dir = meta_data["base_dir_path"]
        # blank_image_path = meta_data["image_path"]["blank_image"]
        # ## Card image as a background
        # doc_cleaned_img_file = os.path.join(base_dir, blank_image_path) # "cleaned.png")
        # document_bg_img = Image.open(doc_cleaned_img_file).convert("RGBA")
        img_pil = document_bg_img.copy()
        bounds = []
        for line_annonation in line_annotations:
            line_coordinates = line_annonation["coordinates"]
            x1, y1, x2, y2 = line_coordinates
            bounds.append([x1, x2, y1, y2])

        # this function call the visualize method to draw the boxes around text
        draw_boxes(img_pil, bounds=bounds, color='lime', width=1, text_font_size=14, text_fill_color="orange", draw_text_idx=True)
        # display(img_pil)
        line_visualized_out_dir = os.path.join(
            os.path.dirname(out_dir_cards), "visualized", "lines"
        )
        os.makedirs(line_visualized_out_dir, exist_ok=True)
        img_pil.save(
            os.path.join(
                line_visualized_out_dir, f"{image_index:04}_visualized.png"
            )
        )
    return True


def main():
    """
    Description: Main function
    """
    import psutil
    cpu_workers = psutil.cpu_count(logical=False)

    ## ---------------------------------------------------------------------
    # Opening JSON file
    # json_meta_file = "./data/document-id-template/UAE-identity-card-front/meta.json"
    json_meta_file = "./data/document-id-template/Qatar-residency-id-front/meta.json"
    with open(json_meta_file, encoding="utf-8") as json_file:
        meta_data = json.load(json_file)
    
    # print(meta_data)
    # total_images_2_generate = 1 # 50 # 2
    total_images_2_generate = int(input("Total images to generate: "))

    ## Step 1: Generate data
    generate_data_and_cards(
        meta_data=meta_data, 
        total_images_2_generate=total_images_2_generate,
        thread_count=cpu_workers,
    )

    ## Step 2: Generate cards -- render data
    print(f"\nProcessign step 2: Rendering cards")
    # for image_index in tqdm(range(0, total_images_2_generate)):
    #     generate_data_and_cards(
    #         image_index=image_index,
    #         meta_data=meta_data,
    #         is_generate_text=False,
    #         is_render_text_on_card=True,
    #     )
    worker = generate_data_and_cards  # function to map
    kwargs = {
        'meta_data': meta_data,
        'is_generate_text': False,
        'is_render_text_on_card': True
    }
    jobs = range(0, total_images_2_generate)  # file_rel_paths

    result = process_map(partial(worker, **kwargs), jobs, max_workers=cpu_workers, chunksize=1)
    return result


if __name__ == "__main__":
    from timeit import default_timer as timer
    from datetime import timedelta

    start = timer()

    main()

    end = timer()
    print("Execution time: ", timedelta(seconds=end-start))