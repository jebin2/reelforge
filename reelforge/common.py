import os
import re
from PIL import Image, ImageFilter
from jebin_lib import utils


def clean_text(text):
    return utils.clean_text(text)

def only_alpha(text: str) -> str:
    return utils.only_alpha(text)

def is_same_sentence(sentence_1, sentence_2, threshold=0.9):
    return utils.is_same_sentence(sentence_1, sentence_2, threshold)

def manage_gpu(size_gb: float = 0, gpu_index: int = 0, action: str = "check"):
    return utils.manage_gpu(size_gb, gpu_index, action)

def is_gpu_available(verbose=True):
    return utils.is_gpu_available(verbose)

def get_device(is_vision=False):
    return utils.get_device(is_vision)

def resize_with_smart_crop(img_path, output_path, target_w=1080, target_h=1920, center_xy=None):
    with Image.open(img_path) as img:
        w, h = img.size
        new_h = 1080
        new_w = int(w * (new_h / h))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        if new_w > target_w:
            if center_xy:
                cx, _ = center_xy
                left = max(0, min(new_w - target_w, int(cx - target_w // 2)))
            else:
                left = crop_entropy(resized, target_w)
            foreground = resized.crop((left, 0, left + target_w, new_h))
        else:
            foreground = Image.new("RGB", (target_w, new_h), (0, 0, 0))
            offset_x = (target_w - new_w) // 2
            foreground.paste(resized, (offset_x, 0))
        blurred_bg = img.resize((target_w, target_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(20))
        y = (target_h - new_h) // 2
        blurred_bg.paste(foreground, (0, y))
        blurred_bg.save(output_path, "JPEG", quality=95)
        return output_path
