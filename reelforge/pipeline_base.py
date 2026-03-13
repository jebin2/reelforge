from abc import ABC, abstractmethod
import json
import os
from custom_logger import logger_config
from jebin_lib import utils
from .categories.base import CategoryBase
from . import config  # needed for BASE_PATH in _to_rel


def _to_rel(path):
    """Convert an absolute path to relative (relative to BASE_PATH) for JSON storage."""
    if path and os.path.isabs(path):
        return os.path.relpath(path, config.BASE_PATH)
    return path


class PipelineBase(ABC):
    def __init__(self, file, category, sync_callback=None):
        self.file = file
        self.category = CategoryBase.get_category(category, self)
        self.sync_callback = sync_callback
        self._wrap_methods()
        self.set_all_paths()


    def set_all_paths(self):
        # all paths
        self.file_parent_dir_path = os.path.dirname(self.file)
        self.file_base_name_without_ext = os.path.splitext(os.path.basename(self.file))[0]
        self.file_base_name_with_ext = os.path.basename(self.file)
        self.file_path = os.path.join(self.file_parent_dir_path, self.file_base_name_without_ext)
        self.compressed_file_path = self.file_path + "_compressed.mp4"
        self.audio_path = self.file_path + "_fully_extracted.mp3"
        self.stt_json_path = self.file_path + "_fully_extracted.json"
        self.intro_path = self.file_path + "_fully_extracted_intro.json"
        self.outro_path = self.file_path + "_fully_extracted_outro.json"
        self.scene_dialogue_map_path = self.file_path + "_fully_extracted_scene_dialogue_map.json"
        self.frame_dir_path = self.file_path + "_fully_extracted_frames"
        os.makedirs(self.frame_dir_path, exist_ok=True)
        self.caption_generator_dir_path = self.file_path + "_caption_generator"
        os.makedirs(self.caption_generator_dir_path, exist_ok=True)
        self.recap_title_desc_path = self.file_path + "_recap_title_desc.json"
        self.recap_audio_path = self.file_path + "_recap_audio.wav"
        self.sentences_json_path = self.file_path + "_sentences.json"
        self.match_scenes_online_path = self.file_path + "_match_scenes_online.json"
        self.choose_best_frames_json_path = self.file_path + "_choose_best_frames.json"
        self.sentence_frames_dir_path = self.file_path + "_sentence_frames"
        os.makedirs(self.sentence_frames_dir_path, exist_ok=True)
        self.sentence_media_dir_path = self.file_path + "_sentence_media"
        os.makedirs(self.sentence_media_dir_path, exist_ok=True)
        self.insight_face_manager_path = self.file_path + "_insight_face_manager"
        self.musicgen_path = self.file_path + "_musicgen.wav"
        self.merged_audio_path = self.file_path + "_merged_audio.wav"
        self.final_video_path = self.file_parent_dir_path + "/output.mp4"
        self.progress_path = self.file_parent_dir_path + "/progress.json"

    # ------------------------------------------------------------------ progress

    def _get_progress(self):
        if not os.path.exists(self.progress_path):
            return {}
        with open(self.progress_path, 'r') as f:
            return json.load(f)

    def _save_progress(self, data):
        with open(self.progress_path, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------ misc

    def allowed_create(self):
        return self.category.allowed_create()

    def is_processed(self):
        progress_json = self._get_progress()
        return progress_json.get("PROCESSED", False)

    def is_published(self):
        progress_json = self._get_progress()
        return progress_json.get("PUBLISHED", False)

    def _wrap_methods(self):
        if not self.sync_callback:
            return
        for attr_name in dir(self.__class__):
            if attr_name.startswith('_') or attr_name in ["is_processed", "is_published", "set_all_paths", "get_service", "set_service", "allowed_create", "process"]:
                continue
            attr = getattr(self, attr_name)
            if callable(attr):
                setattr(self, attr_name, self._create_sync_wrapper(attr))

    def _create_sync_wrapper(self, func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if self.sync_callback:
                logger_config.info(f"Sync callback for {func.__name__}")
                self.sync_callback()
            return result
        return wrapper

    @abstractmethod
    def process(self):
        pass
