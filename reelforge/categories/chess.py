from .base import CategoryBase
from .. import config

class Chess(CategoryBase):
    def __init__(self, video_processor_obj):
        super().__init__("chess", video_processor_obj)

    def allowed_create(self):
        return False

    def allowed_to_publish_in_twitter(self):
        return False

    def allowed_to_publish_in_yt(self):
        return True

    def get_yt_title(self):
        progress = self.video_processor_obj._get_progress()
        return f"How to solve Chess.com today's daily puzzle : {progress['date']}  #ChessPuzzles #ChessTactics #challenges"

    def get_yt_description(self, title=None):
        return f"#chess #chessbreakdown #chessshorts #{title}"

    def get_yt_tags(self):
        tags = ['ChessBreakdown', 'ChessAnalysis', 'ChessReview', 'recap']
        tags.append("shorts")
        return tags

    def get_cred_token_file_name(self):
        return "ytcredentials.json", "yttoken.json"
