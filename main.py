from jebin_lib import load_env, utils
load_env()

import gc
import sys
import os
import shutil
import traceback

from jebin_lib import HFBucketClient
from custom_logger import logger_config
from reelforge import config
from reelforge.pipeline.processor import VideoProcessor
from reelforge.publisher.publisher_processor import PublisherProcessor

class ContentCreator:

    def __init__(self, local_only=True, remote_only=False, is_publisher=False):
        self.hf_client = HFBucketClient(bucket_id=config.HF_BUCKET_ID) if config.HF_BUCKET_ID else None
        self.local_only = local_only
        self.remote_only = remote_only
        self.is_publisher = is_publisher
        self.setup()

    def setup(self):
        if self.hf_client:
            for category in config.CATEGORY:
                local_cat_path = os.path.join(config.CONTENT_TO_BE_PROCESSED, category)
                if self.is_publisher:
                    if category not in [config.COMIC, config.CHESS]:
                        continue
                    self.hf_client.download_folder(category, local_cat_path)
                elif self.local_only:
                    self.hf_client.upload_folder(local_cat_path, category, delete=True)
                elif self.remote_only:
                    if os.path.isdir(local_cat_path):
                        shutil.rmtree(local_cat_path)
                    self.hf_client.download_folder(category, local_cat_path)
                else:
                    self.hf_client.download_folder(category, local_cat_path)
                    self.hf_client.upload_folder(local_cat_path, category)

    def sync(self, local_path, remote_path):
        if self.hf_client:
            self.hf_client.upload_folder(local_path, remote_path)

    def force_sync(self, local_path, remote_path):
        if self.hf_client:
            self.hf_client.upload_folder(local_path, remote_path, delete=True)

    def run(self):
        all_files = utils.list_files_recursive(config.CONTENT_TO_BE_PROCESSED)
        if self.is_publisher:
            # For publisher: scan progress.json files; PublisherProcessor reads FINAL_VIDEO_PATH from them
            video_files = [f for f in all_files if os.path.basename(f) == "progress.json"]
        else:
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
                
                # Robust category extraction: first folder after CONTENT_TO_BE_PROCESSED
                rel_path = utils.to_rel(file, config.CONTENT_TO_BE_PROCESSED)
                category = rel_path.split(os.sep)[0]

                video_folder = os.path.dirname(file)
                remote_path = utils.to_rel(video_folder, config.CONTENT_TO_BE_PROCESSED)
                kwargs = dict(
                    file=utils.to_rel(file, config.BASE_PATH),
                    category=category,
                    sync_callback=lambda lp=video_folder, rp=remote_path: self.sync(lp, rp)
                )
                if self.is_publisher:
                    kwargs['force_sync_callback'] = lambda lp=video_folder, rp=remote_path: self.force_sync(lp, rp)
                pipeline_instance = pipeline(**kwargs)
                if self.is_publisher or pipeline_instance.allowed_create():
                    pipeline_instance.run()
            except (Exception, SystemExit) as e:
                logger_config.error(f"Failed to process {file}: {e}")
                logger_config.error(traceback.format_exc())
            finally:
                gc.collect()

def main():
    os.chdir(config.BASE_PATH)

    local_only = '--localonly' in sys.argv
    remote_only = '--remoteonly' in sys.argv
    is_publisher = '--publisher' in sys.argv
    one_pass = '--onepass' in sys.argv

    # remove directory start with thread_id_*
    for entry in os.scandir(config.BASE_PATH):
        if entry.name.startswith(('thread_id_', 'temp', 'chat_bot_ui_handler_logs')) and entry.is_dir():
            utils.remove_directory(entry.path)

    while True:
        creator = None
        try:
            creator = ContentCreator(
                local_only=local_only,
                remote_only=remote_only,
                is_publisher=is_publisher
            )
            creator.run()
        except (Exception, SystemExit) as e:
            logger_config.error(f"Failed to process: {e}")
            logger_config.error(traceback.format_exc())
            del e
        finally:
            del creator
            gc.collect()

        if one_pass:
            break
        logger_config.info("Sleeping for 60 seconds", seconds=60)

if __name__ == '__main__':
    main()
