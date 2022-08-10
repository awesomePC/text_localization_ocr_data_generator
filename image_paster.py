"""
Script to paste word/line text region images on big background images. To generate text localization data.
"""
import os
from PIL import Image
from pathlib import Path
from tqdm.auto import tqdm
from loguru import logger

# Own python utilities package
from nb_utils.file_dir_handling import list_files ## pip install nb_utils


def paste_text_imgs_on_bg(
    dir_text_imgs, dir_bg, dir_result="./output", 
    factor_multiply_text_images=1,
    margin_top=10, margin_left=10, margin_bottom=10, 
    margin_right=10, margin_position="absolute",
    ):
    """
    Paste text image either single word or line image generated using text recognition data generator
    on background image
    """
    lst_text_images_2_paste = list_files(dir_text_imgs, filter_ext=[".png", ".jpg", ".jpeg"])
    background_images = list_files(dir_bg, filter_ext=[".png", ".jpg", ".jpeg"])
    os.makedirs(dir_result, exist_ok=True)

    ## Make sure folder path exists
    if not os.path.exists(dir_text_imgs):
        logger.error("Error.. directory: {lst_text_images_2_paste} not exists..")
        return

    if not os.path.exists(dir_bg):
        logger.error("Error.. background images directory: {lst_text_images_2_paste} not exists..")
        return

    # import pdb;pdb.set_trace()

    ## Additional functionality
    ## List replicate items n times, to increase volume
    if factor_multiply_text_images >= 2:
        replicated_list = []
        lst_text_images_2_paste = lst_text_images_2_paste * factor_multiply_text_images

    for image in tqdm(background_images): 
        parent_bg_image = Image.open(image)
        p = Path(image)
        bg_width, bg_height = parent_bg_image.size
        # logger.debug(f"background image width : { bg_width } and height {bg_height}")
        
        # ## margin around pasted image
        # margin_top = 50
        # margin_left = 50
        # margin_bottom = 50
        # margin_right = 50

        # margin_position = "absolute" ## 1) absolute: value used as pixel 2) relative: Value considered as percentage and actual pixel margin will be calculated based on bg image height and width

        if margin_position == "relative":
            margin_top = int(margin_top * bg_height / 100)
            margin_left = int(margin_left * bg_width / 100)
            margin_bottom = int(margin_bottom * bg_height / 100)
            margin_right = int(margin_right * bg_width / 100)

        ## image placing position which can change every time 
        ## Current position of cursor -- update it after pasting image
        current_x = 0
        current_y = 0

        ## Line element max_height 
        line_item_height = 0
        is_first_item_on_line = True # Is it first item on line
        for child_image_file in lst_text_images_2_paste:
            c = Path(child_image_file)
            child_image = Image.open(child_image_file)
            child_img_width, child_img_height = child_image.size

            ## Compute position to paste image
            ## Add margin around child image -- text image
            new_width = margin_left + child_img_width + margin_right
            new_height = margin_top + child_img_height + margin_bottom

            ## Set line item height
            line_item_height = max(new_height, line_item_height)

            new_position_x = current_x + margin_left
            new_position_x2 = current_x + new_width

            if is_first_item_on_line:
                new_position_y = current_y + margin_top
                new_position_y2 = current_y + new_height
                
                ## set flag to false -- so top margin will not be added for second word on same line
                is_first_item_on_line = False
            else:
                new_position_y = current_y
                new_position_y2 = current_y

            ## Check if it's going outside image
            ## First horizontal
            if (new_position_x2 >= bg_width):
                ## Put it on new line
                new_position_x = margin_left
                new_position_y = new_position_y + line_item_height
                new_position_x2 = new_width
                new_position_y2 = new_position_y2 + line_item_height

                ## Reset line height flag
                line_item_height = 0

                ## Reset flag
                ## After switching to new line -- the text you render will be first item
                is_first_item_on_line = True

            parent_bg_image.paste(child_image,(new_position_x, new_position_y), mask=child_image)

            ## Update current coordinates -- outer loop value
            current_x = new_position_x2
            current_y = new_position_y

            # if (p_width - position_width) > c_width :
            #       print(p_width,position_width)
            #       parent_bg_image.paste(c_image,(position_width,position_height), mask=c_image)
            #       position_width = position_width + c_width + 40 
            # else :
            #       print(" Line width Over")
            #       position_height = position_height + c_height + 100 
            #       position_width = 0 
            #       parent_bg_image.paste(c_image,(position_width,position_height))
            #       position_width = position_width + c_width + 40 
            #       # parent_bg_image.paste(c_image,(position_width,position_height))
            #       print (" Printing on next line")
            #       if position_height > p_height : 
            #         print("height over")
            #         break
        
        out_filepath = os.path.join(dir_result, f"{p.stem}{c.stem}{c.suffix}")
        parent_bg_image.save(out_filepath)
          
def main():
    """
    """
    from argparse import ArgumentParser
    # Initialize parser
    parser = ArgumentParser()

    parser.add_argument(
      "-td", "--dir_text_imgs", type=str, required=False, 
      default="./data/word-images-generated-by-text-recognition-data-generator",
      help = """Source directory to read text images for pasting it in background images. 
      Source text images is generated using 
      1) text recognition data generator script 
      2) Or for realistic text, you can crop word or line area of text and remove background using bg.remove,
        after that for obtaining text coordinates of that background removed image you can either use any ocr engine 
        or use PPOCRLabel to manually draw the box around text to get coordinates.
      """
    )
    parser.add_argument(
      "-bgd", "--dir_bg", type=str, required=False, 
      default="./data/background-2-place-text/plain",
      help = "directory containing background images.. ex. template id cards, blank old paper page photo etc.."
    )
    parser.add_argument(
      "-rd", "--dir_result", type=str, required=False,
      default="./out/output_result",
      help = "directory to store final images"
    )
    parser.add_argument(
      "-mf", "--factor_multiply_text_images", type=int, default=1, required=False, 
      help="If word images are less and if you want to increase count use this factor.. value 2 means word images will be replicated 2 times."
    )
    parser.add_argument(
      "-mt", "--margin_top", type=int, default=5, required=False, 
      help="Top margin to add to the pasted image"
    )
    parser.add_argument(
      "-ml", "--margin_left", type=int, default=5, required=False, 
      help="Left margin to add to the pasted image"
    )
    parser.add_argument(
      "-mb", "--margin_bottom", type=int, default=5, required=False, 
      help="Bottom margin to add to the pasted image"
    )
    parser.add_argument(
      "-mr", "--margin_right", type=int, default=5, required=False, 
      help="Right margin to add to the pasted image"
    )
    parser.add_argument(
      "-mp", "--margin_position", type=str, default="absolute", required=False, 
      help="Margin position: "
    )

    args = parser.parse_args()
  
    paste_text_imgs_on_bg(
      dir_text_imgs=args.dir_text_imgs,
      dir_bg=args.dir_bg,
      dir_result=args.dir_result,
      factor_multiply_text_images=int(args.factor_multiply_text_images),
      margin_top=args.margin_top,
      margin_left=args.margin_left,
      margin_bottom=args.margin_bottom,
      margin_right=args.margin_right,
      margin_position=args.margin_position,
    )

if __name__ == "__main__":
    main()
