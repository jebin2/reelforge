from pathlib import Path
import os
import torch
import difflib
import pynvml, signal, gc
import re
from PIL import Image, ImageFilter

def get_device(is_vision=False):
    device = None
    if not is_vision and os.getenv("USE_CPU_IF_POSSIBLE", None):
        device = "cpu"
    else:
        device = "cuda" if is_gpu_available() else "cpu"

    if device == "cpu":
        torch.cuda.is_available = lambda: False

    return device

def only_alpha(text: str) -> str:
    # Keep only alphabetic characters (make lowercase to ignore case)
    return re.sub(r'[^a-zA-Z]', '', text).lower()

def is_same_sentence(sentence_1, sentence_2, threshold=0.9):
    # Clean both
    sentence_1 = only_alpha(sentence_1)
    sentence_2 = only_alpha(sentence_2)

    similarity = difflib.SequenceMatcher(None, sentence_1, sentence_2).ratio()
    logger_config.info(f"is_same_sentence :: similarity-{similarity}")
    return similarity > threshold

def manage_gpu(size_gb: float = 0, gpu_index: int = 0, action: str = "check"):
    """
    Manage GPU memory:
      - check       → just prints memory + process table
      - clear_cache → clears PyTorch cache
      - kill        → kills all GPU processes
    """
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)

        free_gb = info.free / 1024**3
        total_gb = info.total / 1024**3

        print(f"\nGPU {gpu_index}: Free {free_gb:.2f} GB / Total {total_gb:.2f} GB")

        # Show processes
        processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        print("\nActive GPU Processes:")
        print(f"{'PID':<8} {'Process Name':<40} {'Used (GB)':<10}")
        print("-" * 60)
        for p in processes:
            used_gb = p.usedGpuMemory / 1024**3
            proc_name = pynvml.nvmlSystemGetProcessName(p.pid).decode(errors="ignore")
            print(f"{p.pid:<8} {proc_name:<40} {used_gb:.2f}")

        if action == "clear_cache":
            try:
                gc.collect()
                gc.collect()
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                time.sleep(1)
                print("\n🧹 Cleared PyTorch CUDA cache")
            except ImportError:
                print("\n⚠️ PyTorch not installed, cannot clear cache.")

        elif action == "kill":
            for p in processes:
                proc_name = pynvml.nvmlSystemGetProcessName(p.pid).decode(errors="ignore")
                try:
                    os.kill(p.pid, signal.SIGKILL)
                    print(f"❌ Killed {p.pid} ({proc_name})")
                except Exception as e:
                    print(f"⚠️ Could not kill {p.pid}: {e}")
            manage_gpu(action="clear_cache")
        gc.collect()
        gc.collect()
        return free_gb > size_gb
    except: return False

def is_gpu_available(verbose=True):
    if not torch.cuda.is_available():
        if verbose:
            print("CUDA not available.")
        return False
    
    try:
        # Try a tiny allocation to check if GPU is free & usable
        torch.empty(1, device="cuda")
        if verbose:
            print(f"CUDA available. Using device: {torch.cuda.get_device_name(0)}")
        return True
    except RuntimeError as e:
        if "CUDA-capable device(s) is/are busy or unavailable" in str(e) or \
           "CUDA error" in str(e):
            if verbose:
                print("CUDA detected but busy/unavailable. Please CPU.")
            return False
        raise  # re-raise if it's some other unexpected error

def clean_text(text):
    text = re.sub(r"\\+", "", text)
    return re.sub(r'\s+', ' ', text).strip()


def resize_with_smart_crop(img_path, output_path, target_w=1080, target_h=1920, center_xy=None):
    """
    Resize image to target_h=1080 height, add blurred background to target_h=1920.
    - If image width > target_w, crop:
        - Using entropy (default)
        - OR around provided center_xy = (x, y)
    """
    with Image.open(img_path) as img:
        w, h = img.size

        # Step 1: resize foreground → height = 1080
        new_h = 1080
        new_w = int(w * (new_h / h))
        resized = img.resize((new_w, new_h), Image.LANCZOS)

        # Step 2: crop horizontally if needed
        if new_w > target_w:
            if center_xy:
                # Crop around provided x coordinate
                cx, _ = center_xy
                left = max(0, min(new_w - target_w, int(cx - target_w // 2)))
            else:
                # Entropy-based crop
                left = crop_entropy(resized, target_w)
            foreground = resized.crop((left, 0, left + target_w, new_h))
        else:
            # Pad horizontally if narrower
            foreground = Image.new("RGB", (target_w, new_h), (0, 0, 0))
            offset_x = (target_w - new_w) // 2
            foreground.paste(resized, (offset_x, 0))

        # Step 3: create blurred background
        blurred_bg = img.resize((target_w, target_h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(20))

        # Step 4: paste foreground vertically centered
        y = (target_h - new_h) // 2
        blurred_bg.paste(foreground, (0, y))

        blurred_bg.save(output_path, "JPEG", quality=95)
        return output_path