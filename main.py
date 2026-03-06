from jebin_lib import load_env, utils
load_env()

import sys
import json
import os, shutil
from pathlib import Path
import traceback

from jebin_lib import HFDatasetClient
from custom_logger import logger_config
from video_recap import common, config
from video_recap.video_processor import VideoProcessor

class VideoRecapPipeline:

    def __init__(self, local_only=True):
        self.hf_client = HFDatasetClient(repo_id=config.PUBLISH_HF_REPO_ID)
        self.sync_states = {} # Path -> Signature
        self.local_only = local_only
        self.setup()

    def setup(self):
        for cat in config.CATEGORY:
            if self.local_only:
                # Overwrite remote with local — skip download, push with delete
                local_cat_path = os.path.join(config.VIDEO_TO_BE_PROCESSED, cat)
                self.hf_client.upload_folder(local_cat_path, cat, delete_patterns=["*"])
                self.sync_states[local_cat_path] = self._get_dir_fingerprint(local_cat_path)
            else:
                self.sync(cat)
                self.hf_client.download_folder(cat, config.VIDEO_TO_BE_PROCESSED)
                # Snapshot the directory after download so downloaded files
                # are included in the baseline and don't trigger a re-upload.
                local_cat_path = os.path.join(config.VIDEO_TO_BE_PROCESSED, cat)
                self.sync_states[local_cat_path] = self._get_dir_fingerprint(local_cat_path)

    def _get_dir_fingerprint(self, path):
        """Returns a frozenset of (relpath, mtime_ns, size) for all files."""
        if not os.path.exists(path):
            return frozenset()
        result = set()
        for root, _, files in os.walk(path):
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    st = os.stat(fpath)
                    result.add((os.path.relpath(fpath, path), st.st_mtime_ns, st.st_size))
                except OSError:
                    continue
        return frozenset(result)

    def sync(self, category):
        local_cat_path = os.path.join(config.VIDEO_TO_BE_PROCESSED, category)
        current_fp = self._get_dir_fingerprint(local_cat_path)

        if self.sync_states.get(local_cat_path) == current_fp:
            return  # Nothing changed since last upload

        self.hf_client.upload_folder(local_cat_path, category)
        # Capture fingerprint AFTER upload so any files the upload itself
        # modifies (e.g. git-lfs pointer files) are included in the baseline.
        self.sync_states[local_cat_path] = self._get_dir_fingerprint(local_cat_path)

    def run(self):
        all_files = utils.list_files_recursive(config.VIDEO_TO_BE_PROCESSED)
        # Filter videos: only if folder name and file name match
        video_files = [
            f for f in all_files 
            if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')) 
            and os.path.splitext(os.path.basename(f))[0] == os.path.basename(os.path.dirname(f))
        ]
        
        for idx, file in enumerate(video_files):
            try:
                logger_config.info(f"Processing {idx + 1}/{len(video_files)}")
                
                # Robust category extraction: first folder after VIDEO_TO_BE_PROCESSED
                rel_path = os.path.relpath(file, config.VIDEO_TO_BE_PROCESSED)
                category = rel_path.split(os.sep)[0]
            
                videoProcessor = VideoProcessor(
                    file=file, 
                    category=category,
                    sync_callback=lambda c=category: self.sync(c)
                )
                videoProcessor.process()
            except Exception as e:
                logger_config.error(f"Failed to process {file}: {e}")
                logger_config.error(traceback.format_exc())

            # # main video
            # videoProcessor.source = "input_video"
            # videoProcessor.extract_audio()
            # videoProcessor.generate_stt()
            # videoProcessor.ignore_credit_scenes()
            # videoProcessor.generate_frames()
            # videoProcessor.generate_captions()

            # # Recap
            # videoProcessor.source = "recap"
            # videoProcessor.generate_recap()
            # videoProcessor.fix_spelling_mistakes()
            # videoProcessor.generate_recap_audio()
            # videoProcessor.generate_title_and_description()

            # # Recap video
            # videoProcessor.source = "recap"
            # videoProcessor.match_scenes()
            # videoProcessor.choose_best_frames()
            # videoProcessor.choose_emojis()
            # videoProcessor.create_clip_for_frames()
            # videoProcessor.focus_characters_clip()

            # # Recap audio
            # videoProcessor.source = "recap"
            # videoProcessor.create_bg_music()
            # videoProcessor.merge_audio()

            # # Recap video
            # videoProcessor.source = "recap"
            # videoProcessor.create_final_video()

if __name__ == '__main__':
    local_only = '--localonly' in sys.argv
    VideoRecapPipeline(local_only=local_only).run()
