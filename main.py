from jebin_lib import load_env, utils, ensure_hf_mounted, sync_to_hf
load_env()

import gc
import shutil
import sys
import os
import traceback
from custom_logger import logger_config

from reelforge import config
from reelforge.pipeline.processor import VideoProcessor
from reelforge.publisher.publisher_processor import PublisherProcessor


class ContentCreator:

    def __init__(self, is_publisher=False):
        self.is_publisher = is_publisher
        ensure_hf_mounted(config.HF_BUCKET_ID, config.HF_TOKEN, config.HF_MOUNT_PATH)

    def run(self):
        all_files = utils.list_files_recursive(config.CONTENT_TO_BE_PROCESSED)
        if self.is_publisher:
            video_files = [f for f in all_files if os.path.basename(f) == "progress.json"]
        else:
            video_files = [
                f for f in all_files
                if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm'))
                and os.path.splitext(os.path.basename(f))[0] == os.path.basename(os.path.dirname(f))
            ]

        for idx, file in enumerate(video_files):
            try:
                pipeline = PublisherProcessor if self.is_publisher else VideoProcessor
                logger_config.info(f"Processing {pipeline.__name__} {idx + 1}/{len(video_files)} : {file}")

                rel_path = utils.to_rel(file, config.CONTENT_TO_BE_PROCESSED)
                category = rel_path.split(os.sep)[0]

                pipeline_instance = pipeline(
                    file=utils.to_rel(file, config.CONTENT_TO_BE_PROCESSED),
                    category=category,
                )
                if self.is_publisher or pipeline_instance.allowed_create():
                    subpath = utils.to_rel(pipeline_instance.file_parent_dir_path, config.CONTENT_TO_BE_PROCESSED)
                    sync_to_hf(config.CONTENT_TO_BE_PROCESSED, config.HF_MOUNT_PATH, subpath=subpath)
                    pipeline_instance.run()
            except (Exception, SystemExit) as e:
                logger_config.error(f"Failed to process {file}: {e}")
                logger_config.error(traceback.format_exc())
            finally:
                gc.collect()

def main():
    os.chdir(config.BASE_PATH)

    is_publisher = '--publisher' in sys.argv
    one_pass = '--onepass' in sys.argv

    for entry in os.scandir(config.BASE_PATH):
        if entry.name.startswith(('thread_id_', 'temp', 'chat_bot_ui_handler_logs')) and entry.is_dir():
            utils.remove_directory(entry.path)

    os.makedirs(config.TEMP_PATH, exist_ok=True)

    while True:
        creator = None
        try:
            creator = ContentCreator(is_publisher=is_publisher)
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
