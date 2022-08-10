"""
Script to unreshape text -- get original text from reshaped format
link:
https://github.com/mpcabd/python-arabic-reshaper/issues/74

Purpose:
Textrecognition datageneartor writes label in contextual form, and it creating some issues, so
converting it to isolated form many ocr engines default dictionaries working fine
"""
from python_arabic_reshaper import arabic_reshaper
from bidi.algorithm import get_display

text_to_be_unreshape = "ﻥﻮﺴﻨﺑﻭﺭ"
unreshaped_text = arabic_reshaper.unreshape(text_to_be_unreshape)

# print(unreshaped_text)
print(get_display(unreshaped_text))