from .base import CategoryBase
from .. import config

class Comic(CategoryBase):
    def __init__(self, processor_obj):
        super().__init__(config.COMIC, processor_obj)

    def allowed_create(self):
        return False

    def allowed_to_publish_in_twitter(self):
        return False

    def allowed_to_publish_in_yt(self):
        return True

    def get_yt_description(self):
        return (
            "Join me as we break down the latest comics, diving deep into its themes, "
            "character development, and key plot points.\n\n"
            "#comics #ComicBreakdown #ComicAnalysis #ComicReview #ComicNarration #ComicStorytelling"
        )

    def get_yt_tags(self):
        return ['ComicBreakdown', 'ComicAnalysis', 'ComicReview', 'ComicNarration', 'ComicStorytelling', 'comics']

    def get_cred_token_file_name(self):
        return "ytcrcredentials.json", "ytcrtoken.json"
