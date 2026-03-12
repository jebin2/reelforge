import os
import json
import shutil
from custom_logger import logger_config
from ..pipeline_base import PipelineBase
from .. import config


class PublisherProcessor(PipelineBase):
    def __init__(self, file, category, sync_callback=None, force_sync_callback=None):
        super().__init__(file, category, sync_callback)
        self.services = {}
        self.force_sync_callback = force_sync_callback or sync_callback

    def get_service(self, key):
        return self.services.get(key)

    def set_service(self, key, service):
        self.services[key] = service

    def _cleanup_folder(self):
        for entry in os.scandir(self.file_parent_dir_path):
            if entry.path == self.progress_path:
                continue
            if entry.is_dir(follow_symlinks=False):
                shutil.rmtree(entry.path)
            else:
                os.remove(entry.path)
        logger_config.info(f"Cleaned up folder: {self.file_parent_dir_path}")

    def _mark_published(self):
        progress = self._get_progress()
        progress['published'] = True
        with open(self.progress_path, 'w') as f:
            json.dump(progress, f, indent=4, ensure_ascii=False)

    def process(self):
        if self.is_published():
            logger_config.info(f"Already published: {self.file}")
            self._cleanup_folder()
            if self.force_sync_callback:
                self.force_sync_callback()
            return

        progress = self._get_progress()
        if not progress:
            logger_config.warning(f"No progress file found for {self.file}, skipping.")
            return

        final_video_path = os.path.join(config.VIDEO_TO_BE_PROCESSED, progress.get("FINAL_VIDEO_PATH", ""))
        if not os.path.exists(final_video_path):
            logger_config.warning(f"Final video not found: {final_video_path}, skipping.")
            return

        if not self.category.allowed_publish_time():
            logger_config.info(f"Not allowed to publish at this time for category {self.category}, skipping.")
            return

        published = False

        if self.category.allowed_to_publish_in_yt():
            from .youtube_publusher import YoutubePublisher
            yt = YoutubePublisher(self)
            if yt.publish(progress, final_video_path):
                published = True

        if self.category.allowed_to_publish_in_twitter():
            from .twitter_publisher import TwitterPublisher
            twitter = TwitterPublisher(self)
            if twitter.publish(progress, final_video_path):
                published = True

        if published:
            self._mark_published()
            self._cleanup_folder()
            if self.force_sync_callback:
                self.force_sync_callback()
