from moviepy import VideoFileClip, CompositeVideoClip
from custom_logger import logger_config
from . import zoom_text
from jebin_lib import utils

def place_emoji_on_video(video_path, img_path, emoji_text, output_path, position=None, opacity=None):
    # ---------------------
    # Load base video
    # ---------------------
    base_video = VideoFileClip(video_path)
    duration = base_video.duration
    video_w, video_h = base_video.w, base_video.h

    # bottom 30% placement box
    bottom_area_h = int(video_h * 0.30)

    # ---------------------
    # Create Emoji Clip
    # ---------------------
    _, emoji_clip = zoom_text.zoom_with_text(
        img_path,
        zoom_loc=[0, 0, 1080, 1920],
        word=emoji_text,
        duration=duration
    )
    if not emoji_clip:
        logger_config.warning(f"Failed to create emoji clip, re-encoding source video.: {emoji_text}")
        utils.run_ffmpeg(["ffmpeg", "-y", "-i", video_path,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-vf", "fps=24",
            "-an", output_path])
        return output_path

    # Resize emoji to fit comfortably in bottom 30%
    emoji_target_h = int(bottom_area_h * 0.8)
    emoji_clip = emoji_clip.resized(height=emoji_target_h)

    # Position at bottom center
    if not position:
        emoji_x = (video_w - emoji_clip.w) // 2
        emoji_y = video_h - bottom_area_h + (bottom_area_h - emoji_clip.h) // 2
        position = (emoji_x, emoji_y)

    if position == "center":
        # diameter = 70% of video width
        target_size = int(video_w * 0.70)

        # perfect square resize
        emoji_clip = emoji_clip.resized(width=target_size)

        # video center
        position = ('center', 'center')

    if opacity is not None:
        emoji_clip = emoji_clip.with_opacity(opacity)

    emoji_clip = emoji_clip.with_position(position)

    # ---------------------
    # Composite
    # ---------------------
    final = CompositeVideoClip([base_video, emoji_clip])
    final = final.with_duration(duration)

    # Export final video
    utils.write_videofile(final, output_path)

    return output_path
