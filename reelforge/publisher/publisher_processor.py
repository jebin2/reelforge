import os
import json
import shutil
from custom_logger import logger_config
from ..pipeline_base import PipelineBase
from .. import config
from jebin_lib import utils

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

    def _mark_published(self, publish_at_ist=None):
        progress = self._get_progress()
        progress['PUBLISHED'] = True
        if publish_at_ist:
            progress['PUBLISH_AT'] = publish_at_ist
        with open(self.progress_path, 'w') as f:
            json.dump(progress, f, indent=4, ensure_ascii=False)

    def _get_used_publish_dates(self):
        """Return set of dates (YYYY-MM-DD IST) already scheduled or published in this category."""
        used = set()
        category_folder = os.path.dirname(self.file_parent_dir_path)
        if not os.path.isdir(category_folder):
            return used
        for entry in os.scandir(category_folder):
            if not entry.is_dir() or entry.path == self.file_parent_dir_path:
                continue
            progress_file = os.path.join(entry.path, "progress.json")
            if not utils.file_exists(progress_file):
                continue
            try:
                with open(progress_file) as f:
                    import json_repair
                    p = json_repair.loads(f.read())
                publish_at = p.get("PUBLISH_AT", "")
                if publish_at:
                    used.add(publish_at[:10])  # YYYY-MM-DD
            except Exception:
                pass
        return used

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

        if not progress.get("PROCESSED", False):
            logger_config.warning(f"Not processed: {self.file}, skipping.")
            return

        final_video_path = utils.to_abs(progress.get("FINAL_VIDEO_PATH", ""), config.BASE_PATH)
        if not utils.file_exists(final_video_path):
            logger_config.warning(f"Final video not found: {final_video_path}, skipping.")
            return

        from datetime import datetime, timedelta

        used_dates = self._get_used_publish_dates()
        next_publish_time = self.category.next_allowed_publish_datetime(used_dates)

        publish_at_utc = None
        publish_at_ist = None
        if next_publish_time:
            publish_at_utc = next_publish_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ist_time = next_publish_time + timedelta(hours=5, minutes=30)
            publish_at_ist = ist_time.strftime("%Y-%m-%d %H:%M:%S")
            logger_config.info(f"Scheduling publish at {publish_at_ist} IST for {self.file}")

        published = False

        if self.category.allowed_to_publish_in_yt():
            from .youtube_publusher import YoutubePublisher
            yt = YoutubePublisher(self)

            thumbnail_path = utils.to_abs(progress.get("THUMBNAIL_PATH", ""), config.BASE_PATH)
            if thumbnail_path and not utils.file_exists(thumbnail_path):
                thumbnail_path = None

            if yt.publish(progress, final_video_path, publish_at_utc=publish_at_utc, thumbnail_path=thumbnail_path):
                published = True

            shorts_video_path = utils.to_abs(progress.get("SHORTS_VIDEO_PATH", ""), config.BASE_PATH)
            if shorts_video_path and utils.file_exists(shorts_video_path):
                yt.publish(progress, shorts_video_path, publish_at_utc=publish_at_utc)

        if self.category.allowed_to_publish_in_twitter():
            from .twitter_publisher import TwitterPublisher
            twitter = TwitterPublisher(self)
            if twitter.publish(progress, final_video_path):
                published = True

        if published:
            self._mark_published(publish_at_ist=publish_at_ist)
            self._cleanup_folder()
            if self.force_sync_callback:
                self.force_sync_callback()
