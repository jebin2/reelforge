import os
import platform

_arch = platform.machine()
_pkg_dir = os.path.dirname(__file__)

BASE_PATH = os.path.dirname(_pkg_dir)

TEMP_PATH = os.path.join(BASE_PATH, 'temp')
os.makedirs(TEMP_PATH, exist_ok=True)

HF_BUCKET_ID = os.getenv("HF_BUCKET_ID")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MOUNT_PATH = os.getenv("HF_MOUNT_PATH")

CONTENT_TO_BE_PROCESSED = HF_MOUNT_PATH if HF_MOUNT_PATH else os.path.join(BASE_PATH, 'content_to_be_processed')
if not HF_MOUNT_PATH:
    os.makedirs(CONTENT_TO_BE_PROCESSED, exist_ok=True)

ANIME="anime"
MOVIE="movie"
CHESS="chess"
COMIC="comic"

CATEGORY=[ANIME, MOVIE, CHESS, COMIC]

TEXT_FONT = BASE_PATH + "/reelforge/Fonts/font_1.ttf"

FPS = 24
TRANSITION_FRAMES = 18 # must match TRANSITION_FRAMES in remotion-reels/src/transitions.ts
TRANSITION_DURATION = TRANSITION_FRAMES / FPS
IMAGE_SIZE = (1920, 1080)

# Prompts
INTRO_SONG_DETECTION_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/intro_song_detection_system_prompt.md"
OUTRO_SONG_DETECTION_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/outro_song_detection_system_prompt.md"
ANIME_SHORT_RECAP_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/anime_short_recap_system_prompt.md"
TITLE_AND_DESC_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/title_and_desc_system_prompt.md"
MOVIE_SHORT_RECAP_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/movie_short_recap_system_prompt.md"
SCENE_MATCHING_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/scene_matching_system_prompt.md"
JSON_VALIDATOR_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/json_validator_system_prompt.md"
KEYWORD_EXTRACT_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/keyword_extract_system_prompt.md"
CREATE_MUSIC_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/create_music_system_prompt.md"
CLIP_ANIMATION_SYSTEM_PROMPT = BASE_PATH + "/reelforge/prompt/clip_animation_system_prompt.md"

MODEL_NAME="gemini-3-flash-preview"
MODEL_NAME_LITE="gemini-flash-lite-latest"

SUBPROCESS_ENV = {**os.environ, 'PYTHONUNBUFFERED': '1', 'CUDA_LAUNCH_BLOCKING': '1', 'USE_CPU_IF_POSSIBLE': 'true'}