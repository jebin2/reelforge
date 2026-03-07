import os
import json
from custom_logger import logger_config
from ..pipeline_base import PipelineBase


class PublisherProcessor(PipelineBase):
    def __init__(self, file, category, sync_callback=None):
        super().__init__(file, category, sync_callback)
        self.services = {}

    def get_service(self, key):
        return self.services.get(key)

    def set_service(self, key, service):
        self.services[key] = service

    def _mark_published(self):
        progress = self._get_progress()
        progress['published'] = True
        with open(self.progress_path, 'w') as f:
            json.dump(progress, f, indent=4, ensure_ascii=False)

    def process(self):
        if self.is_published():
            logger_config.info(f"Already published: {self.file}")
            return

        progress = self._get_progress()
        if not progress:
            logger_config.warning(f"No progress file found for {self.file}, skipping.")
            return

        if not os.path.exists(self.final_video_path):
            logger_config.warning(f"Final video not found: {self.final_video_path}, skipping.")
            return

        published = False

        if self.category.allowed_to_publish_in_yt():
            from .youtube_publusher import YoutubePublisher
            yt = YoutubePublisher(self)
            if yt.publish(progress, self.final_video_path):
                published = True

        if self.category.allowed_to_publish_in_twitter():
            from .twitter_publisher import TwitterPublisher
            twitter = TwitterPublisher(self)
            if twitter.publish(progress, self.final_video_path):
                published = True

        if published:
            self._mark_published()
