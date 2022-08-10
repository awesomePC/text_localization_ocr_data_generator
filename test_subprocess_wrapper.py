"""
Test subprocess execution in Python
info:
https://stackoverflow.com/questions/89228/how-to-execute-a-program-or-call-a-system-command
"""
import os,sys
import subprocess

# result = subprocess.run(["python", "--version"], capture_output=True, text=True, shell=True)
# print(result)

# result = subprocess.run(["python", "image_paster.py", "-mf", "5"], capture_output=True, text=True, shell=True)
# print(result)

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
cmd = [
    "--dict", "./data/document-id-template/UAE-identity-card-front/dicts/text-2--الإمارات العربية المتحدة.txt",
    "--language", "ar",
    "--margins", "3",
    "--format", "26",
    "--font", "TextRecognitionDataGenerator/trdg/fonts/ar/Times-New-Roman.ttf",
    "--output_dir", "./out",
]

## final command
final_cmd = py_cmd + cmd + common_cmd_params
# print(" ".join(final_cmd))

result = subprocess.run(final_cmd, shell=True, capture_output=False, text=True, stderr=subprocess.STDOUT)
print(result)