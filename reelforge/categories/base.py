from abc import ABC, abstractmethod
import json
import os
from .. import config

class CategoryBase(ABC):
    def __init__(self, name, video_processor_obj):
        self.name = name
        self.video_processor_obj = video_processor_obj

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return super().__eq__(other)

    def allowed_create(self):
        return True

    @staticmethod
    def get_category(name, video_processor_obj):
        if name == config.MOVIE:
            from .movie import Movie
            return Movie(video_processor_obj)
        elif name == config.ANIME:
            from .anime import Anime
            return Anime(video_processor_obj)
        elif name == config.CHESS:
            from .chess import Chess
            return Chess(video_processor_obj)
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
        full_result = self.video_processor_obj.generate_recap()
        with open(self.video_processor_obj.progress_path, "w") as f:
            json.dump({
                    "FINAL_VIDEO_PATH": os.path.relpath(self.video_processor_obj.final_video_path, config.VIDEO_TO_BE_PROCESSED),
                    "CREDENTIAL_NAME": self.get_cred_token_file_name()[0],
                    "TOKEN_NAME":self.get_cred_token_file_name()[1],
                    "YOUTUBE_TITLE": full_result.get("youtube_title", self.get_yt_title()),
                    "TWITTER_POST": full_result.get("twitter_post", self.get_yt_description())
                }, f, indent=4, ensure_ascii=False
            )
