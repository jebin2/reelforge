from .category_base import CategoryBase
from . import config
import json

class Movie(CategoryBase):
    def __init__(self):
        super().__init__("movie")

    def get_fyi(self, file_base_name_without_ext):
        return f'This is a Movie frame from the movie called {file_base_name_without_ext}'

    def review_system_prompt(self):
        with open(config.MOVIE_SHORT_RECAP_SYSTEM_PROMPT, 'r') as file:
            return file.read()

    def allowed_to_publish_in_x(self):
        return False

    def get_yt_description(self, title=None):
        return f"#movie #moviebreakdown #movieshorts #{title}"

    def get_yt_tags(self):
        tags = ['MovieBreakdown', 'MovieAnalysis ', 'MovieReview', 'recap']
        tags.append("shorts")

        return tags

    def create_progress_file(self, progress_path, youtube_title = None, twitter_post = None):
        with open(progress_path, "w") as f:
            json.dump({
                    "CREDENTIAL_NAME": "ytmrcredentials.json",
                    "TOKEN_NAME":"ytmrtoken.json",
                    "YOUTUBE_TITLE": youtube_title,
                    "TWITTER_POST": twitter_post
                }, f, indent=4, ensure_ascii=False
            )