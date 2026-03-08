from jebin_lib import load_env, utils
load_env()

import sys
import json
import os, shutil
from pathlib import Path
import traceback

from jebin_lib import HFDatasetClient
from custom_logger import logger_config
from reelforge import config
from reelforge.pipeline.processor import VideoProcessor
from reelforge.publisher.publisher_processor import PublisherProcessor

class ContentCreator:

    def __init__(self, local_only=True, is_publisher=False):
        self.hf_client = HFDatasetClient(repo_id=config.PUBLISH_HF_REPO_ID) if config.PUBLISH_HF_REPO_ID else None
        self.sync_states = {} # Path -> Signature
        self.local_only = local_only
        self.is_publisher = is_publisher
        self.setup()

    def _snapshot_video_folders(self, cat_path):
        """Snapshot per-video-folder fingerprints so initial sync skips unchanged folders."""
        if not os.path.isdir(cat_path):
            return
        for entry in os.scandir(cat_path):
            if entry.is_dir():
                self.sync_states[entry.path] = self._get_dir_fingerprint(entry.path)

    def setup(self):
        if self.hf_client:
            for cat in config.CATEGORY:
                local_cat_path = os.path.join(config.VIDEO_TO_BE_PROCESSED, cat)
                if self.local_only:
                    # Overwrite remote with local — skip download, push with delete
                    self.hf_client.upload_folder(local_cat_path, cat, delete_patterns=["*"])
                else:
                    self.hf_client.download_folder(cat, config.VIDEO_TO_BE_PROCESSED)
                # Snapshot each video subfolder so syncs don't re-upload immediately
                self._snapshot_video_folders(local_cat_path)

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

    def sync(self, local_path, remote_path):
        if self.hf_client:
            current_fp = self._get_dir_fingerprint(local_path)
            if self.sync_states.get(local_path) == current_fp:
                return  # Nothing changed since last upload
            self.hf_client.upload_folder(local_path, remote_path)
            self.sync_states[local_path] = self._get_dir_fingerprint(local_path)

    def force_sync(self, local_path, remote_path):
        if self.hf_client:
            self.hf_client.upload_folder(local_path, remote_path, delete_patterns=["*"])
            self.sync_states[local_path] = self._get_dir_fingerprint(local_path)

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
                pipeline = PublisherProcessor if self.is_publisher else VideoProcessor
                logger_config.info(f"Processing {pipeline.__name__} {idx + 1}/{len(video_files)} : {file}")
                
                # Robust category extraction: first folder after VIDEO_TO_BE_PROCESSED
                rel_path = os.path.relpath(file, config.VIDEO_TO_BE_PROCESSED)
                category = rel_path.split(os.sep)[0]

                video_folder = os.path.dirname(file)
                remote_path = os.path.relpath(video_folder, config.VIDEO_TO_BE_PROCESSED)
                kwargs = dict(
                    file=file,
                    category=category,
                    sync_callback=lambda lp=video_folder, rp=remote_path: self.sync(lp, rp)
                )
                if self.is_publisher:
                    kwargs['force_sync_callback'] = lambda lp=video_folder, rp=remote_path: self.force_sync(lp, rp)
                pipeline_instance = pipeline(**kwargs)
                if self.is_publisher or pipeline_instance.allowed_create():
                    pipeline_instance.process()
            except Exception as e:
                logger_config.error(f"Failed to process {file}: {e}")
                logger_config.error(traceback.format_exc())

if __name__ == '__main__':
    local_only = '--localonly' in sys.argv
    is_publisher = '--publisher' in sys.argv
    one_pass = '--onepass' in sys.argv

    cc = ContentCreator(
        local_only=local_only,
        is_publisher=is_publisher
    )
    while True:
        try:
            cc.run()
        except Exception as e:
            logger_config.error(f"Failed to process: {e}")
            logger_config.error(traceback.format_exc())

        if one_pass:
            break
        logger_config.info("Sleeping for 60 seconds", seconds=60)
        time.sleep(60)
        
