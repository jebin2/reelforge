from .category_base import CategoryBase
from . import config

class Anime(CategoryBase):
    def __init__(self, video_processor_obj):
        super().__init__("anime", video_processor_obj)

    def get_fyi(self, file_base_name_without_ext):
        return f'This is an Anime frame from the anime called {file_base_name_without_ext}'

    def review_system_prompt(self):
        with open(config.ANIME_SHORT_RECAP_SYSTEM_PROMPT, 'r') as file:
            return file.read()

    def allowed_to_publish_in_twitter(self):
        return False

    def allowed_to_publish_in_yt(self):
        return True

    def get_yt_description(self, title=None):
        return f"#anime #animebreakdown #animeshorts #{title}"

    def get_yt_tags(self):
        tags = ['AnimeBreakdown', 'AnimeAnalysis ', 'AnimeReview', 'recap']
        tags.append("shorts")

        return tags

    def get_cred_token_file_name(self):
        return "ytarcredentials.json", "ytartoken.json"