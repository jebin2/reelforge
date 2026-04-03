from abc import ABC, abstractmethod
import json
import json_repair
import os
from custom_logger import logger_config
from jebin_lib import utils
from .categories.base import CategoryBase
from . import config  # needed for BASE_PATH in _to_rel

import hashlib
import tempfile

def _lock_path_for(folder: str) -> str:
    key = hashlib.md5(os.path.abspath(folder).encode()).hexdigest()
    return os.path.join(tempfile.gettempdir(), f"reelforge_{key}.lock")


class PipelineBase(ABC):
    def __init__(self, file, category):
        self.file = file
        self.category = CategoryBase.get_category(category, self)
        self.set_all_paths()


    def set_all_paths(self):
        # resolve to absolute so all derived paths are correct regardless of cwd
        self.file = utils.to_abs(self.file, config.CONTENT_TO_BE_PROCESSED)
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
        self.longform_video_path = self.file_parent_dir_path + "/longform_output.mp4"
        self.long_recap_path = self.file_path + "_long_recap.json"
        self.longform_media_dir_path = self.file_path + "_longform_media"
        os.makedirs(self.longform_media_dir_path, exist_ok=True)
        self.longform_sentences_json_path = self.file_path + "_longform_sentences.json"
        self.longform_match_scenes_path = self.file_path + "_longform_match_scenes.json"
        self.longform_best_frames_json_path = self.file_path + "_longform_best_frames.json"
        self.longform_sentence_frames_dir_path = self.file_path + "_longform_sentence_frames"
        os.makedirs(self.longform_sentence_frames_dir_path, exist_ok=True)
        self.progress_path = self.file_parent_dir_path + "/progress.json"

    # ------------------------------------------------------------------ progress

    def _get_progress(self):
        if not os.path.exists(self.progress_path):
            return {}
        with open(self.progress_path, 'r') as f:
            return json_repair.loads(f.read())

    def _save_progress(self, data):
        with open(self.progress_path, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------ misc

    def allowed_create(self):
        return self.category.allowed_create()

    def is_processed(self):
        progress_json = self._get_progress()
        return progress_json.get("PROCESSED", False)

    def _acquire_lock(self) -> bool:
        lock_path = _lock_path_for(self.file_parent_dir_path)
        try:
            with open(lock_path, 'x') as f:
                f.write(str(os.getpid()))
            return True
        except FileExistsError:
            try:
                with open(lock_path) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                return False
            except (ProcessLookupError, ValueError, OSError):
                os.remove(lock_path)
                return self._acquire_lock()

    def _release_lock(self):
        lock_path = _lock_path_for(self.file_parent_dir_path)
        try:
            os.remove(lock_path)
        except FileNotFoundError:
            pass

    def run(self):
        if not self._acquire_lock():
            logger_config.warning(f"Folder locked by another process, skipping: {self.file_parent_dir_path}")
            return
        try:
            self.process()
        finally:
            self._release_lock()

    @abstractmethod
    def process(self):
        pass
