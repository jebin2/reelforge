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
        elif name == config.COMIC:
            from .comic import Comic
            return Comic(processor_obj)
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

    def next_allowed_publish_datetime(self, used_dates=None):
        from datetime import datetime, timedelta, timezone
        import random

        WED, FRI, SUN = 2, 4, 6
        TARGET_DAYS = {WED, FRI, SUN}

        TIMES = [(3, 30), (14, 30)]
        hour, minute = random.choice(TIMES)

        used_dates = used_dates or set()
        now_utc = datetime.now(timezone.utc)

        # Start from today (midnight UTC)
        candidate = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

        for _ in range(30):
            if candidate.weekday() in TARGET_DAYS:
                slot = candidate.replace(hour=hour, minute=minute)

                date_str = slot.strftime("%Y-%m-%d")

                if slot > now_utc and date_str not in used_dates:
                    return slot

            candidate += timedelta(days=1)

        return None