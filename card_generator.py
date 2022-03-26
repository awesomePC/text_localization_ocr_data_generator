import os,sys
import subprocess
import imutils
from PIL import Image

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
    dim = None
    (w, h) = img.size

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


def main():
    """
        Description: Main function
    """
    ## Pasting generated word image
    doc_cleaned_img_file = "./data/document-id-template/UAE-identity-card-front/cleaned.png"
    document_bg_img = Image.open(doc_cleaned_img_file).convert("RGBA")

    ## ----------------------------------------------------------------------
    output_dir = "out"
    height = 26

    cmd = [
        "--dict", "./data/document-id-template/UAE-identity-card-front/dicts/text-2--الإمارات العربية المتحدة.txt",
        "--language", "ar",
        "--margins", "3",
        "--format", str(height),
        "--font", "TextRecognitionDataGenerator/trdg/fonts/ar/Times-New-Roman.ttf",
        "--output_dir", output_dir,
    ]

    ## final command
    final_cmd = py_cmd + cmd + common_cmd_params
    # print(" ".join(final_cmd))

    result = subprocess.run(final_cmd, shell=True, capture_output=False, text=True, stderr=subprocess.STDOUT)
    # print(result)
    ## ----------------------------------------------------------------------

    # word_image_file = os.path.join(output_dir, f"United Arab Emirates_0.png")
    # word_image_file = os.path.join(output_dir, f"Identity Card_0.png")
    # word_image_file = os.path.join(output_dir, f"ﺓﺪﺤﺘﻤﻟﺍ ﺔﻴﺑﺮﻌﻟﺍ ﺕﺍﺭﺎﻣﻹﺍ ﺔﻟﻭﺩ_0.png")
    word_image_file = os.path.join(output_dir, f"0.png")
    word_img = Image.open(word_image_file).convert("RGBA")
    word_img = resize_pil_image(word_img, height=22)

    # new_position_x, new_position_y = 14, 10
    # new_position_x, new_position_y = 55, 42
    new_position_x, new_position_y = 245, 7
    document_bg_img.paste(word_img,(new_position_x, new_position_y), mask=word_img)
    out_filepath = os.path.join(output_dir, f"result_doc.png")
    document_bg_img.save(out_filepath)

if __name__ == "__main__":
    main()