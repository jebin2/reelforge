from .category_base import CategoryBase
from . import config
import json

class Anime(CategoryBase):
    def __init__(self):
        super().__init__("anime")

    def get_fyi(self, file_base_name_without_ext):
        return f'This is an Anime frame from the anime called {file_base_name_without_ext}'

    def review_system_prompt(self):
        with open(config.ANIME_SHORT_RECAP_SYSTEM_PROMPT, 'r') as file:
            return file.read()

    def allowed_to_publish_in_x(self):
        return False

    def get_yt_description(self, title=None):
        return f"#anime #animebreakdown #animeshorts #{title}"

    def get_yt_tags(self):
        tags = ['AnimeBreakdown', 'AnimeAnalysis ', 'AnimeReview', 'recap']
        tags.append("shorts")

        return tags

    def create_progress_file(self, progress_path, youtube_title = None, twitter_post = None):
        with open(progress_path, "w") as f:
            json.dump({
                    "CREDENTIAL_NAME": "ytarcredentials.json",
                    "TOKEN_NAME":"ytartoken.json",
                    "YOUTUBE_TITLE": youtube_title,
                    "TWITTER_POST": twitter_post
                }, f, indent=4, ensure_ascii=False
            )