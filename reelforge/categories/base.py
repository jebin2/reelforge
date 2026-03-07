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

    @staticmethod
    def get_category(name, video_processor_obj):
        if name == "movie":
            from .movie import Movie
            return Movie(video_processor_obj)
        elif name == "anime":
            from .anime import Anime
            return Anime(video_processor_obj)
        else:
            raise ValueError(f"Invalid category: {name}")

    @abstractmethod
    def get_cred_token_file_name(self):
        pass

    def create_progress_file(self):
        full_result = self.video_processor_obj.generate_recap()
        with open(self.video_processor_obj.progress_path, "w") as f:
            json.dump({
                    "FINAL_VIDEO_PATH": os.path.relpath(self.video_processor_obj.final_video_path, os.path.dirname(config.BASE_PATH)),
                    "CREDENTIAL_NAME": self.get_cred_token_file_name()[0],
                    "TOKEN_NAME":self.get_cred_token_file_name()[1],
                    "YOUTUBE_TITLE": full_result.get("youtube_title", "watch now"),
                    "TWITTER_POST": full_result.get("twitter_post", "watch now")
                }, f, indent=4, ensure_ascii=False
            )
