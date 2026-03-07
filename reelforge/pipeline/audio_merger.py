from moviepy import AudioFileClip, CompositeAudioClip, concatenate_audioclips
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, MultiplyVolume
import numpy as np
from .. import common
import subprocess, sys, os

def get_audio_rms(audio_clip, sample_duration=1.0):
    """
    Calculate RMS of an audio clip by sampling a segment.
    To avoid processing very long audio, we sample the first `sample_duration` seconds.
    """
    duration = min(sample_duration, audio_clip.duration)
    audio_segment = audio_clip.subclipped(0, duration)
    audio_array = audio_segment.to_soundarray(fps=44100)
    return np.sqrt(np.mean(audio_array**2))

def calculate_bg_volume(main_rms, bg_rms):
    """
    Calculate background music volume based on both main audio and background music RMS levels.
    """
    # Base volume adjustment based on main audio level
    if main_rms > 0.03:  # High main audio level
        base_volume = 0.3
    elif main_rms > 0.01:  # Medium main audio level
        base_volume = 0.4
    else:  # Low main audio level
        base_volume = 0.5

    # Adjust based on background music loudness
    if bg_rms > 0.15:  # Very loud background music
        bg_volume = base_volume * 0.2  # Reduce significantly
    elif bg_rms > 0.08:  # Moderately loud background music
        bg_volume = base_volume * 0.4  # Reduce moderately
    elif bg_rms > 0.03:  # Normal background music
        bg_volume = base_volume * 0.6  # Keep base volume
    elif bg_rms > 0.01:  # Quiet background music
        bg_volume = base_volume * 0.8  # Boost slightly
    else:  # Very quiet background music
        bg_volume = base_volume * 1.2  # Boost more

    # Ensure volume stays within reasonable bounds
    bg_volume = max(0.1, min(0.8, bg_volume))

    return bg_volume

def process(audio_path_1, audio_path_2, output_path):
    original_audio = AudioFileClip(audio_path_1)
    new_audio = AudioFileClip(audio_path_2)

    if new_audio.duration > original_audio.duration:
        new_audio = new_audio.subclipped(0, original_audio.duration)

    elif new_audio.duration < original_audio.duration:
        fade_dur = 1.0
        clips = []
        t = 0
        while t < original_audio.duration:
            part = new_audio.subclipped(0, min(new_audio.duration, original_audio.duration - t))
            part = part.with_effects([AudioFadeIn(fade_dur), AudioFadeOut(fade_dur)])
            clips.append(part)
            t += part.duration
        new_audio = concatenate_audioclips(clips).with_duration(original_audio.duration)

    # Calculate RMS for both audio sources
    main_rms = get_audio_rms(original_audio)
    bg_rms = get_audio_rms(new_audio)

    # Calculate optimal background volume
    bg_volume = calculate_bg_volume(main_rms, bg_rms)

    print(f"Main RMS: {main_rms:.4f}, BG RMS: {bg_rms:.4f}, BG Volume: {bg_volume:.2f}")

    # Apply volumes
    new_audio = new_audio.with_effects([MultiplyVolume(bg_volume)])
    original_audio = original_audio.with_effects([MultiplyVolume(0.8)])

    # Combine audio tracks
    combined_audio = CompositeAudioClip([original_audio, new_audio])

    combined_audio.write_audiofile(output_path)

    return output_path
