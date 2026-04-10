import logging
import uuid
from collections import Counter
from functools import cache

import arcade
from PIL import Image


@cache
def hue(image_path: str) -> int:
    """Get most common hue in important pixels (saturated, not transparent…).

    Args:
        image_path: path of the image to analyze

    Returns:
        the most common hue (rounded to tens)
    """
    image = Image.open(image_path)
    alphas = image.getdata(band=3)
    hsv_image = image.convert("HSV")
    hues = hsv_image.getdata(band=0)
    saturations = hsv_image.getdata(band=1)
    values = hsv_image.getdata(band=2)
    important_hues = [
        hue // 10 * 10
        for hue, saturation, value, alpha in zip(
            hues, saturations, values, alphas, strict=False
        )
        if saturation > 50 and value > 50 and alpha != 0
    ]
    counter = Counter(important_hues)
    return counter.most_common(1)[0][0]


@cache
def hue_changed_texture(image_path: str, target_hue: int) -> arcade.Texture:
    logging.info("Managing %s", image_path)

    target_hue = target_hue * 256 // 360

    original_image = Image.open(image_path)
    original_hue = hue(image_path)
    offset_hue = 256 + target_hue - original_hue
    alpha_channel = original_image.split()[-1]
    hsv_image = original_image.convert("HSV")
    h, s, v = hsv_image.split()
    hue_data = h.point(lambda i: (i + offset_hue) % 256)
    adjusted_hue_image = Image.merge("HSV", (hue_data, s, v))
    adjusted_hue_image_rgb = adjusted_hue_image.convert("RGB")
    final_image = Image.merge("RGBA", (*adjusted_hue_image_rgb.split(), alpha_channel))
    return arcade.Texture(name=str(uuid.uuid4()), image=final_image)
