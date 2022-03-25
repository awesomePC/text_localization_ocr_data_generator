import os
from PIL import Image, ImageDraw, ImageFont

fontsize = 32
# txt = "Hello Nivratti"
txt = u"دولة الإمارات العربية المتحدة"

image = Image.new("RGBA", (600,150), (255,255,255))
draw = ImageDraw.Draw(image)
# font = ImageFont.truetype("./TextRecognitionDataGenerator/trdg/fonts/latin/Roboto-Bold.ttf", fontsize)
font = ImageFont.truetype("./TextRecognitionDataGenerator/trdg/fonts/ar/timesbd.ttf", fontsize)

# draw.text((10, 0), txt, (0,0,0), font=font)
draw.text((10, 0), txt, (0,0,0), font=font, stroke_width=1)

image.save("./out/test_font_rendering.png")
