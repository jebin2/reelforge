import os
import platform

_arch = platform.machine()
_pkg_dir = os.path.dirname(__file__)

BASE_PATH = os.path.dirname(_pkg_dir)

TEMP_PATH = os.path.join(BASE_PATH, 'temp')
os.makedirs(TEMP_PATH, exist_ok=True)

VIDEO_TO_BE_PROCESSED = os.path.join(BASE_PATH, 'video_to_be_processed')
os.makedirs(VIDEO_TO_BE_PROCESSED, exist_ok=True)

ANIME="anime"
MOVIE="movie"
CHESS="chess"

CATEGORY=[ANIME, MOVIE, CHESS]

PUBLISH_HF_REPO_ID = os.getenv("PUBLISH_HF_REPO_ID")

TEXT_FONT = BASE_PATH + "/reelforge/Fonts/font_1.ttf"

FPS = 24
IMAGE_SIZE = (1920, 1080)

INTRO_SONG_DETECTION_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/intro_song_detection_system_prompt.md"
OUTRO_SONG_DETECTION_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/outro_song_detection_system_prompt.md"
ANIME_SHORT_RECAP_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/anime_short_recap_system_prompt.md"
TITLE_AND_DESC_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/title_and_desc_system_prompt.md"
MOVIE_SHORT_RECAP_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/movie_short_recap_system_prompt.md"
SCENE_MATCHING_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/scene_matching_system_prompt.md"
JSON_VALIDATOR_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/json_validator_system_prompt.md"
KEYWORD_EXTRACT_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/keyword_extract_system_prompt.md"
CREATE_MUSIC_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/create_music_system_prompt.md"

MODEL_NAME="gemini-3.1-flash-lite-preview"
ALL_MODEL_NAME=["gemini-3-flash-preview", "gemini-3.1-pro-preview"]

SUBPROCESS_ENV = {**os.environ, 'PYTHONUNBUFFERED': '1', 'CUDA_LAUNCH_BLOCKING': '1', 'USE_CPU_IF_POSSIBLE': 'true'}