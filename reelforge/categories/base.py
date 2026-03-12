from abc import ABC, abstractmethod
import json
import os
from .. import config

class CategoryBase(ABC):
    def __init__(self, name, processor_obj):
        self.name = name
        self.processor_obj = processor_obj

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return super().__eq__(other)

    def allowed_create(self):
        return True

    @staticmethod
    def get_category(name, processor_obj):
        if name == config.MOVIE:
            from .movie import Movie
            return Movie(processor_obj)
        elif name == config.ANIME:
            from .anime import Anime
            return Anime(processor_obj)
        elif name == config.CHESS:
            from .chess import Chess
            return Chess(processor_obj)
        else:
            raise ValueError(f"Invalid category: {name}")

    @abstractmethod
    def get_cred_token_file_name(self):
        pass

    def get_yt_title(self):
        return "watch now"

    def get_yt_description(self):
        return "watch now"

    def create_progress_file(self):
        full_result = self.processor_obj.generate_recap()
        youtube_title = full_result.get("youtube_title", self.get_yt_title())
        twitter_post = full_result.get("twitter_post", self.get_yt_description())

        progress = self.processor_obj._get_progress()
        progress.update({
            "FINAL_VIDEO_PATH": os.path.relpath(
                self.processor_obj.final_video_path, config.VIDEO_TO_BE_PROCESSED
            ),
            "SHORTS_VIDEO_PATH": None,
            "YOUTUBE_TITLE": youtube_title,
            "TWITTER_POST": twitter_post,
            "PROCESSED": True
        })
        self.processor_obj._save_progress(progress)

    def allowed_publish_time(self, publish_time_in_utc=None):
        # only on friday, saturday and sunday after 06:00 PM IST (12:30 PM UTC)
        from datetime import datetime

        now = datetime.utcnow()

        if publish_time_in_utc is None:
            publish_time_in_utc = now.time()

        current_weekday = now.weekday()  # Monday is 0, Sunday is 6

        if current_weekday in [4, 5, 6]:  # Friday, Saturday, Sunday
            if (publish_time_in_utc.hour > 12 or
                (publish_time_in_utc.hour == 12 and publish_time_in_utc.minute >= 30)):
                return True

        return False