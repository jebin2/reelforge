from .base import CategoryBase
from .. import config


class Anime(CategoryBase):
    def __init__(self, processor_obj):
        super().__init__(config.ANIME, processor_obj)

    def get_fyi(self, file_base_name_without_ext):
        return f'This is an Anime frame from the anime called {file_base_name_without_ext}'

    def review_system_prompt(self):
        with open(config.ANIME_SHORT_RECAP_SYSTEM_PROMPT, 'r') as file:
            return file.read()

    def get_yt_description(self):
        return "#anime #animebreakdown #animeshorts"

    def get_yt_tags(self):
        return ['AnimeBreakdown', 'AnimeAnalysis', 'AnimeReview', 'recap', 'shorts']

    def get_cred_token_file_name(self):
        return "ytarcredentials.json", "ytartoken.json"
