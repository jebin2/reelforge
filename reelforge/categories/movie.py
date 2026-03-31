import os
from .base import CategoryBase
from .. import config


class Movie(CategoryBase):
    def __init__(self, processor_obj):
        super().__init__("movie", processor_obj)

    def get_recap_source_file(self):
        """Use .txt or .pdf transcript if present alongside the video."""
        base = self.processor_obj.file_path  # full path without extension
        for ext in ['.txt', '.pdf']:
            path = base + ext
            if os.path.exists(path):
                return path
        return None

    def get_fyi(self, file_base_name_without_ext):
        return f'This is a Movie frame from the movie called {file_base_name_without_ext}'

    def review_system_prompt(self):
        with open(config.MOVIE_SHORT_RECAP_SYSTEM_PROMPT, 'r') as file:
            return file.read()

    def get_yt_description(self):
        return "#movie #moviebreakdown #movieshorts"

    def get_yt_tags(self):
        return ['MovieBreakdown', 'MovieAnalysis', 'MovieReview', 'recap']

    def get_cred_token_file_name(self):
        return "ytmrcredentials.json", "ytmrtoken.json"
