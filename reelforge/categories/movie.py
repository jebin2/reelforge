from .base import CategoryBase
from .. import config

class Movie(CategoryBase):
    def __init__(self, video_processor_obj):
        super().__init__("movie", video_processor_obj)

    def get_fyi(self, file_base_name_without_ext):
        return f'This is a Movie frame from the movie called {file_base_name_without_ext}'

    def review_system_prompt(self):
        with open(config.MOVIE_SHORT_RECAP_SYSTEM_PROMPT, 'r') as file:
            return file.read()

    def allowed_to_publish_in_twitter(self):
        return False

    def allowed_to_publish_in_yt(self):
        return True

    def get_yt_description(self):
        return f"#movie #moviebreakdown #movieshorts"

    def get_yt_tags(self):
        tags = ['MovieBreakdown', 'MovieAnalysis ', 'MovieReview', 'recap']
        tags.append("shorts")

        return tags

    def get_cred_token_file_name(self):
        return "ytmrcredentials.json", "ytmrtoken.json"
