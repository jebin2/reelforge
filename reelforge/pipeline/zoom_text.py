import math
from moviepy import ImageClip, CompositeVideoClip, VideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from .. import common
from .. import config
import random
import os
import subprocess
from PIL import ImageSequence, ImageFilter
from custom_logger import logger_config
from jebin_lib import utils

def setup_noto_emoji_repo():
	return utils.setup_git_repo_get_install_pip(
		"https://github.com/jebin2/noto-emoji.git",
		"/tmp/noto-emoji/",
		sparse_dirs=["webp", "png/512"]
	)

def get_emoji_path(emoji: str) -> tuple[bool, str | None]:
	"""Get path to emoji file from noto-emoji collection.
	First checks in webp/ (animated), then png/512 (static).
	Returns (is_animated, path or None).
	"""
	cps = [f"{ord(ch):x}" for ch in emoji][0]
	# filename = "emoji_u" + "_".join(cps) + ".png"  # consistent naming
	filename = "emoji_u" + cps + ".png"  # consistent naming

	# Check animated (webp/)
	webp_path = os.path.join(setup_noto_emoji_repo(), "webp", filename.replace(".png", ".webp"))
	if os.path.exists(webp_path):
		print("webp")
		return True, webp_path

	# Check static (png/512/)
	png_path = os.path.join(setup_noto_emoji_repo(), "png/512", filename)
	if os.path.exists(png_path):
		print("png/512")
		return False, png_path

	# Not found
	return False, None

def smooth_alpha_channel(img, radius=1.0):
    """
    Extracts the alpha channel, applies a very subtle blur to it to remove
    hard jagged edges (aliasing), and merges it back.
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Split channels
    r, g, b, a = img.split()

    # Apply subtle blur to alpha only
    # Radius 1.0 is usually enough to fix jagged edges without making it look blurry
    a = a.filter(ImageFilter.GaussianBlur(radius=radius))

    # Merge back
    return Image.merge('RGBA', (r, g, b, a))

def find_safe_position(text_clip, zoom_loc, video_size):
	"""Find best position for text/emoji around the face box."""
	left, top, right, bottom = zoom_loc
	W, H = video_size
	w, h = text_clip.size  # size of the text/emoji image
	face_center_x = (left + right) // 2
	face_center_y = (top + bottom) // 2

	margin = 20

	# Try Right
	if right + margin + w < W:
		return (right + margin, face_center_y - h // 2)

	# Try Top
	if top - margin - h > 0:
		return (face_center_x - w // 2, top - margin - h)

	# Try Left
	if left - margin - w > 0:
		return (left - margin - w, face_center_y - h // 2)

	# Try Bottom
	if bottom + margin + h < H:
		return (face_center_x - w // 2, bottom + margin)

	# Fallback → Right
	return (right + margin, face_center_y - h // 2)

def create_text_image(text, fontsize=90, color="#4ECDC4", stroke_color="black", stroke_width=5):
	"""Create PIL image with text using font_1"""
	font_path = config.TEXT_FONT
	font = ImageFont.truetype(font_path, fontsize)

	# Use textbbox to get the bounding box of the text
	bbox = font.getbbox(text)
	text_width = bbox[2] - bbox[0]
	text_height = bbox[3] - bbox[1]

	# Create a temporary image to get the actual rendered size with stroke
	temp_img = Image.new('RGBA', (text_width + stroke_width*2, text_height + stroke_width*2), (0,0,0,0))
	temp_draw = ImageDraw.Draw(temp_img)

	# Draw the text with stroke on the temporary image
	temp_draw.text((stroke_width - bbox[0], stroke_width - bbox[1]), text, font=font, fill=color, stroke_width=stroke_width, stroke_fill=stroke_color)

	# Get the bounding box of the non-transparent parts of the image
	img_bbox = temp_img.getbbox()

	if img_bbox:
		# Crop the image to the actual content
		img = temp_img.crop(img_bbox)

		# Add some padding to ensure nothing is clipped
		padded_img = Image.new('RGBA', (img.width + 10, img.height + 10), (0,0,0,0))
		padded_img.paste(img, (5, 5))
		return padded_img
	else:
		# Handle cases where the text might be empty or not render
		return Image.new('RGBA', (1, 1), (0,0,0,0))

def create_emoji_clip(emoji, target_size, duration=5, oversample=3):
	"""Create MoviePy Clip from emoji (animated webp or static png)."""
	is_animated, emoji_path = get_emoji_path(emoji)

	if not emoji_path:
		return None

	# We process images at a higher resolution (oversampling)
	process_size = int(target_size * oversample)

	if is_animated and emoji_path.endswith(".webp"):

		# Load frames from WebP
		pil_img = Image.open(emoji_path)
		frames = []
		durations = []

		for frame in ImageSequence.Iterator(pil_img):
			# Ensure RGBA format
			frame = frame.convert("RGBA")

			# 1. Resize High Quality
			frame = frame.resize((process_size, process_size), Image.Resampling.LANCZOS)

			# 2. Smooth the edges (Anti-aliasing)
			frame = smooth_alpha_channel(frame, radius=1.0)
			frames.append(np.array(frame))
			durations.append(frame.info.get("duration", 100) / 1000.0)  # ms → sec

		# Fallback if duration info missing
		if not any(durations):
			durations = [0.1] * len(frames)

		# Calculate total animation duration
		anim_duration = sum(durations)

		# Calculate cumulative time for each frame
		cumulative_times = [0]
		for d in durations:
			cumulative_times.append(cumulative_times[-1] + d)

		# Helper function to get the correct frame index
		def get_frame_idx(t):
			loop_time = t % anim_duration
			frame_idx = 0
			for i in range(len(cumulative_times) - 1):
				if cumulative_times[i] <= loop_time < cumulative_times[i + 1]:
					frame_idx = i
					break
			return frame_idx

		# Create a function that returns RGB only (without alpha)
		def make_frame_rgb(t):
			frame_idx = get_frame_idx(t)
			return frames[frame_idx][:, :, :3]  # Return only RGB channels

		# Create a function for the alpha mask
		def make_mask(t):
			frame_idx = get_frame_idx(t)
			return frames[frame_idx][:, :, 3] / 255.0  # Return alpha channel normalized

		# Create clip with transparency
		clip = VideoClip(frame_function=make_frame_rgb, duration=duration)
		clip = clip.resized((target_size, target_size))

		mask = VideoClip(frame_function=make_mask, duration=duration, is_mask=True)
		mask = mask.resized((target_size, target_size))

		return clip.with_mask(mask)

	else:
		emoji_img = Image.open(emoji_path).convert("RGBA")
		emoji_img = emoji_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

		emoji_array = np.array(emoji_img)
		return ImageClip(emoji_array, duration=duration, transparent=True)

def pil_to_moviepy_clip(pil_image, duration=5):
	"""Convert PIL Image to MoviePy ImageClip"""
	img_array = np.array(pil_image)
	return ImageClip(img_array, duration=duration, transparent=True)

def bounce_scale(t):
	if t < 0.3:
		return 0.2 + 2*t
	elif t < 0.6:
		return 1.2 - 0.5*(t-0.3)
	else:
		return 1.0

def pulse_scale(t):
	"""Smooth pulsing effect - very popular on YouTube"""
	return 1.0 + 0.15 * math.sin(8 * t)

def neon_glow_scale(t):
	"""Neon glow effect with subtle breathing"""
	return 1.0 + 0.08 * math.sin(6 * t)

def pop_in_scale(t):
	"""Quick pop-in effect - great for attention"""
	if t < 0.2:
		return 0.1 + 4.5 * t  # Quick scale up
	elif t < 0.4:
		return 1.1 - 0.5 * (t - 0.2)  # Small bounce back
	else:
		return 1.0

def float_position(t, base_x, base_y):
	"""Gentle floating motion"""
	return (base_x, base_y + 8 * math.sin(4 * t))

def is_emoji(text):
	"""Simple check if text contains emoji characters"""
	return any(ord(char) > 127 for char in text)

def zoom_with_text(frame_path, zoom_loc, word="", style="neon", duration=5, fontsize=150):
	"""
	Create a short video with PIL-based text animations that properly support emojis
	Uses PNG images for emojis and font_1 for text
	"""
	# Get the display text (emoji or word)
	display_text = word

	left, top, right, bottom = zoom_loc
	face_center_x = (left + right) // 2
	face_center_y = (top + bottom) // 2

	# --- Base image clip ---
	clip = ImageClip(frame_path).with_duration(duration)

	# --- Zoom function focused on zoom_loc ---
	def zoom_func(t):
		scale = 1 + 0.04 * t  # zoom in over duration
		x = face_center_x * (scale - 1)
		y = face_center_y * (scale - 1)
		return (scale, (-x, -y))

	animated = clip.resized(lambda t: zoom_func(t)[0]).with_position(lambda t: zoom_func(t)[1])

	# Color options
	colors = [
		"#E74747", "#FF6B6B", "#4ECDC4", "#2AA0BB", "#36AF77",
		"#C565C5", "#58310B", "#6C5CE7", "#1C533F", "#BB394C",
		"#2ECC71"
	]
	color = random.choice([colors[2], colors[7]])

	# --- Create text/emoji element ---
	text_elements = []
	text_clip = None
	if display_text:
		# Check if it's an emoji or regular text
		if is_emoji(display_text):
			# Use PNG emoji image
			emoji_size = int(fontsize * 1.2)  # Make emoji slightly larger than text would be
			text_clip = create_emoji_clip(display_text, emoji_size, duration=duration)

		if text_clip is None:
			display_text = "" if is_emoji(display_text) else display_text
			# Use font_1 for regular text
			pil_img = create_text_image(display_text, fontsize=fontsize, color=color, stroke_color="black", stroke_width=5)
			text_clip = pil_to_moviepy_clip(pil_img, duration=duration)

		# Apply animation based on style
		if text_clip:
			safe_pos = find_safe_position(text_clip, zoom_loc, clip.size)
			if style == "wobble":
				def wobble_pos(t):
					return (safe_pos[0], safe_pos[1] + 10*math.sin(20*t))
				text_clip = text_clip.with_position(wobble_pos)

			elif style == "pulse":
				text_clip = text_clip.with_position(safe_pos).resized(lambda t: pulse_scale(t))

			elif style == "neon":
				def neon_pos(t):
					return float_position(t, safe_pos[0], safe_pos[1])
				text_clip = text_clip.with_position(neon_pos).resized(lambda t: neon_glow_scale(t))

			elif style == "pop":
				text_clip = text_clip.with_position(safe_pos).resized(lambda t: pop_in_scale(t))

			elif style == "float":
				def float_pos(t):
					return float_position(t, safe_pos[0], safe_pos[1])
				text_clip = text_clip.with_position(float_pos)

			elif style == "bounce":
				text_clip = text_clip.with_position(safe_pos).resized(lambda t: bounce_scale(t))

			elif style == "scream":
				def shake_pos(t):
					if t > 0.1:
						shake_intensity = min(8, t * 20)
						shake_x = shake_intensity * math.sin(50 * t)
						shake_y = shake_intensity * math.cos(40 * t)
					else:
						shake_x, shake_y = 0, 0
					return (safe_pos[0] + shake_x, safe_pos[1] + shake_y)
				text_clip = text_clip.with_position(shake_pos).with_opacity(0.7)

			elif style == "slide_in":
				safe_pos = find_safe_position(text_clip, zoom_loc, clip.size)
				def slide_pos(t):
					if t < 0.5:
						progress = t * 2
						x = (safe_pos[0] + 200) - (180 * progress)
						return (x, safe_pos[1])
					else:
						return (safe_pos[0], safe_pos[1])
				text_clip = text_clip.with_position(slide_pos)

			elif style == "glitch":
				# For glitch effect with emojis, create offset copies
				if is_emoji(display_text):
					red_clip = text_clip.with_position((safe_pos[0] + 15, safe_pos[1] - 6)).with_opacity(0.7)
					blue_clip = text_clip.with_position((safe_pos[0] + 25, safe_pos[1] + 6)).with_opacity(0.7)
					# Apply color filters (this is approximate since we're using PNG)
					text_elements = [red_clip, blue_clip]
				else:
					# For text, create different colored versions
					red_img = create_text_image(display_text, fontsize=fontsize, color="red", stroke_width=0)
					blue_img = create_text_image(display_text, fontsize=fontsize, color="cyan", stroke_width=0)

					red_clip = pil_to_moviepy_clip(red_img, duration=duration).with_position((safe_pos[0], safe_pos[1] - 6)).with_opacity(0.7)
					blue_clip = pil_to_moviepy_clip(blue_img, duration=duration).with_position((safe_pos[0], safe_pos[1] + 6)).with_opacity(0.7)

					text_elements = [red_clip, blue_clip]

			else:
				# Default style
				text_clip = text_clip.with_position(safe_pos)

			if style != "glitch":
				text_elements = [text_clip]

	# --- Final composite ---
	return CompositeVideoClip([animated] + text_elements), text_clip
