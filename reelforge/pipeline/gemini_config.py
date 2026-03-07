from custom_logger import logger_config
import os
from pathlib import Path
from .. import config

pre_model_wrapper=None
try:
	from functools import partial
	from gemiwrap import GeminiWrapper

	pre_model_wrapper = partial(GeminiWrapper, model_name=config.MODEL_NAME)

except:
	logger_config.warning("Gemini Wrapper is not initialised.")
