import os
import sys
import subprocess
from jebin_lib import HFSTTClient, utils, HFTTTClient, HFTTSClient, normalize_loudness
import shutil
import json
from .. import config
from chat_bot_ui_handler import GeminiUIChat, AIStudioUIChat
import json_repair
from .scene_detector import run_transnetv2
from .frame_extractor import map_dialogues_to_scenes, combine_dialogues
from custom_logger import logger_config
from caption_generator.core import MultiTypeCaptionGenerator
from chat_bot_ui_handler import GoogleAISearchChat, QwenUIChat, BingUIChat, BraveAISearch, DuckDuckGoAISearch
from jebin_lib import text_splitter
from .. import common
from . import scene_matcher as sentence_matcher
from browser_manager.browser_config import BrowserConfig
from pathlib import Path
from .gemini_config import pre_model_wrapper
from google import genai
from jebin_lib import merge_audio as merge_music
from . import emoji_placer
from jebin_lib import video_optimizer as ffmpeg_optimise
from ..pipeline_base import PipelineBase

class VideoProcessor(PipelineBase):
    def __init__(self, file, category):
        super().__init__(file, category)

    def get_compressed_file(self):
        """
        Simple, optimized video compression specifically for Google Gemini Pro.
        No complex settings - just compress any video to work perfectly with Gemini Pro.

        Optimizations for Gemini Pro:
        - 2 FPS (perfect for LLM frame analysis)
        - 480x270 resolution (readable but compact)
        - Aggressive compression while maintaining visual clarity
        - Always produces small files suitable for LLM processing

        Parameters:
        - input_path: Path to input video file
        - output_path: Optional output path (auto-generated if None)

        Returns:
        - Path to compressed video file
        """
        if utils.is_valid_video(self.compressed_file_path):
            return self.compressed_file_path

        utils.remove_file(self.compressed_file_path)
        path = Path(self.file)
        name = path.stem

        output_path = Path(self.compressed_file_path)

        # Get input file size
        input_size_mb = os.path.getsize(self.file) / (1024 * 1024)

        # Temporary output file
        tmp_output = output_path.with_suffix(".tmp.mp4")
        if tmp_output.exists():
            tmp_output.unlink()

        logger_config.info(f"Compressing for Gemini Pro: {input_size_mb:.1f}MB → optimized")

        # Gemini Pro optimized FFmpeg command
        cmd = [
            "ffmpeg", "-i", str(self.file),

            # Video: H.264 with aggressive but readable compression
            "-c:v", "libx264",
            "-crf", "32",                    # Aggressive compression, still readable
            "-preset", "veryslow",           # Best compression efficiency

            # Resolution and frame rate optimized for Gemini Pro
            "-vf", "scale=480:270:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=2",

            # Audio: Minimal but present
            "-c:a", "aac",
            "-b:a", "24k",                   # Very low audio bitrate
            "-ac", "1",                      # Mono
            "-ar", "22050",                  # Lower sample rate

            # Optimize for small file size and streaming
            "-movflags", "+faststart",
            "-avoid_negative_ts", "make_zero",

            # Advanced compression settings
            "-x264-params", "keyint=120:scenecut=40:b-adapt=2:me=hex:subme=6:ref=3",

            "-f", "mp4",
            "-y", str(tmp_output)
        ]

        # Execute compression with shared ffmpeg wrapper (non-interactive)
        utils.run_ffmpeg(cmd)
        # Move to final location
        tmp_output.rename(output_path)

        # Show results
        output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        compression_ratio = input_size_mb / output_size_mb if output_size_mb > 0 else 0
        savings_percent = ((input_size_mb - output_size_mb) / input_size_mb * 100) if input_size_mb > 0 else 0

        logger_config.info(f"✅ LLM ready: {output_size_mb:.1f}MB ({compression_ratio:.1f}x smaller, {savings_percent:.1f}% saved)")

        if utils.is_valid_video(self.compressed_file_path):
            return self.compressed_file_path
        else:
            raise Exception(f"Failed to compress video for {self.file}")

    def extract_audio(self):
        audio_file = self.file_path + ".mp3"
        if utils.is_valid_audio(self.audio_path):
            return self.audio_path

        utils.run_ffmpeg(["ffmpeg", "-y", "-i", self.file, audio_file])
        shutil.move(audio_file, self.audio_path)

        if utils.is_valid_audio(self.audio_path):
            return self.audio_path
        else:
            raise Exception(f"Failed to extract audio for {self.file}")

    def generate_stt(self):
        if utils.path_exists(self.stt_json_path) and utils.is_valid_json(self.stt_json_path):
            return self.stt_json_path

        HFSTTClient().transcribe(self.extract_audio())

        if utils.is_valid_json(self.stt_json_path):
            return self.stt_json_path
        else:
            raise Exception(f"Failed to generate STT for {self.file}")

    def ignore_credit_scenes(self):
        with open(self.generate_stt(), 'r') as file:
            segment = json.load(file)["segments"]["word"]

        intro_start_sec = None
        intro_end_sec = None
        if utils.is_valid_json(self.intro_path):
            with open(self.intro_path, 'r') as file:
                intro_json = json.load(file)
                intro_start_sec = intro_json.get("start_sec", None)
                intro_end_sec = intro_json.get("end_sec", None)
                if intro_start_sec is not None:
                    intro_start_sec = float(intro_start_sec)
                if intro_end_sec is not None:
                    intro_end_sec = float(intro_end_sec)

        if intro_start_sec is None or intro_end_sec is None:
            intro_new_seg = []
            for seg in segment:
                if seg["start"] < 300 and seg["end"] < 300:
                    intro_new_seg.append(seg)

            with open(config.INTRO_SONG_DETECTION_SYSTEM_PROMPT , 'r') as file:
                system_prompt = file.read()

            logger_config.info("Intro Song Detection")
            baseUIChat = GeminiUIChat()
            result = json_repair.loads(baseUIChat.quick_chat(
                user_prompt=intro_new_seg,
                system_prompt=system_prompt
            ))
            if not isinstance(result, dict):
                raise ValueError(f"GeminiUIChat returned unexpected response for intro: {result!r}")

            with open(self.intro_path, 'w') as file:
                intro_start_sec = result.get("start_sec", None)
                intro_end_sec = result.get("end_sec", None)
                if not intro_start_sec:
                    intro_start_sec = -1
                if not intro_end_sec:
                    intro_end_sec = -1
                json.dump({
                    "start_sec": intro_start_sec,
                    "end_sec": intro_end_sec,
                    "song_text": result.get("song_text", "")
                }, file, indent=4, ensure_ascii=False)


        outro_start_sec = None
        outro_end_sec = None
        if utils.is_valid_json(self.outro_path):
            with open(self.outro_path, 'r') as file:
                outro_json = json.load(file)
                outro_start_sec = outro_json.get("start_sec", None)
                outro_end_sec = outro_json.get("end_sec", None)
                if outro_start_sec is not None:
                    outro_start_sec = float(outro_start_sec)
                if outro_end_sec is not None:
                    outro_end_sec = float(outro_end_sec)

        if outro_start_sec is None or outro_end_sec is None:
            outro_new_seg = []
            for seg in segment:
                if seg["start"] > segment[-1]["end"] - 300 and seg["end"] > segment[-1]["end"] - 300:
                    outro_new_seg.append(seg)

            with open(config.OUTRO_SONG_DETECTION_SYSTEM_PROMPT , 'r') as file:
                system_prompt = file.read()

            logger_config.info("Outro Song Detection")
            baseUIChat = GeminiUIChat()
            result = json_repair.loads(baseUIChat.quick_chat(
                user_prompt=outro_new_seg,
                system_prompt=system_prompt
            ))
            if not isinstance(result, dict):
                raise ValueError(f"GeminiUIChat returned unexpected response for outro: {result!r}")

            with open(self.outro_path, 'w') as file:
                outro_start_sec = result.get("start_sec", None)
                outro_end_sec = result.get("end_sec", None)
                if not outro_start_sec:
                    outro_start_sec = -1
                if not outro_end_sec:
                    outro_end_sec = -1
                json.dump({
                    "start_sec": outro_start_sec,
                    "end_sec": outro_end_sec,
                    "song_text": result.get("song_text", "")
                }, file, indent=4, ensure_ascii=False)

        return intro_start_sec, intro_end_sec, outro_start_sec, outro_end_sec

    def get_segments(self):
        with open(self.generate_stt(), 'r') as file:
            return json.load(file)["segments"]["segment"]

    def generate_frames(self):
        if utils.is_valid_json(self.scene_dialogue_map_path):
            with open(self.scene_dialogue_map_path, "r") as f:
                data = json.load(f)
                if len(data) >= 100:
                    return data
                else:
                    logger_config.info(f"Scene dialogue map is not valid (len {len(data)} < 100), regenerating...")
                    utils.remove_file(self.scene_dialogue_map_path)

        intro_start_sec, intro_end_sec, outro_start_sec, outro_end_sec = self.ignore_credit_scenes()
        frames = run_transnetv2(
            video_path=self.file,
            start_from_sec=intro_end_sec,
            end_from_sec=outro_start_sec
        )

        logger_config.info("Mapping dialogues to scenes and extracting frames...")
        scene_dialogue_map = map_dialogues_to_scenes(frames, self.get_segments(), self.file, self.frame_dir_path, self.scene_dialogue_map_path)

        if len(scene_dialogue_map) > 0:
            logger_config.info("Combining consecutive scenes with identical dialogues...")
            scene_dialogue_map = combine_dialogues(scene_dialogue_map)
        else:
            raise Exception(f"Failed to generate scene dialogue map for {self.file}")

        with open(self.scene_dialogue_map_path, "w", encoding="utf-8") as f:
            json.dump(scene_dialogue_map, f, indent=4, ensure_ascii=False)

        logger_config.info(f"Mapping saved to {self.scene_dialogue_map_path}")

        return scene_dialogue_map

    def generate_captions(self):
        captionGen = MultiTypeCaptionGenerator(frame_base_path=config.CONTENT_TO_BE_PROCESSED, cache_path=self.caption_generator_dir_path, sources=[GoogleAISearchChat, BraveAISearch, DuckDuckGoAISearch], FYI=self.category.get_fyi(self.file_base_name_without_ext))

        scene_dialogue_map = captionGen.caption_generation(
            self.generate_frames()
        )

        if len([extract_scene for extract_scene in scene_dialogue_map if extract_scene.get("scene_caption") is None or str(extract_scene.get("scene_caption", "")).strip() == ""]) > 0:
            raise Exception(f"Failed to generate captions for {self.file}")
        else:
            with open(self.scene_dialogue_map_path, "w", encoding="utf-8") as f:
                json.dump(scene_dialogue_map, f, indent=4, ensure_ascii=False)
            return scene_dialogue_map

    def _recap_schema(self):
        return genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["data"],
            properties = {
                "data": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
            },
        )

    def _generate_title_and_description(self, full_result):
        if full_result.get("youtube_title", "") == "" or full_result.get("twitter_post", "") == "":
            with open(config.TITLE_AND_DESC_SYSTEM_PROMPT, "r") as f:
                system_prompt = f.read()

            logger_config.info("Title and Description")
            baseUIChat = GeminiUIChat()
            result_title_desc = json_repair.loads(baseUIChat.quick_chat(
                user_prompt=f"""Create a suitable youtube title and twitter post for the below recap
recap: {full_result["recap"]}.""",
                system_prompt=system_prompt
            ))
            if not isinstance(result_title_desc, dict):
                raise ValueError(f"GeminiUIChat returned unexpected response for title/desc: {result_title_desc!r}")
            full_result["youtube_title"] = result_title_desc["youtube_title"]
            full_result["twitter_post"] = result_title_desc["twitter_post"]

            with open(self.recap_title_desc_path, "w", encoding="utf-8") as f:
                json.dump(full_result, f, indent=4, ensure_ascii=False)

        return full_result

    def generate_recap(self):
        full_result = {}
        if utils.is_valid_json(self.recap_title_desc_path):
            with open(self.recap_title_desc_path, "r") as f:
                full_result = json.load(f)

        user_prompt = self.file_base_name_with_ext

        if full_result.get("recap", "") == "":
            recap_source = self.category.get_recap_source_file() or self.get_compressed_file()
            if recap_source != self.get_compressed_file():
                logger_config.info(f"Using transcript file for recap: {recap_source}")

            recap_str = ""
            try_times = 0
            while try_times < 5 and recap_str == "":
                try_times += 1
                logger_config.info(f"Generating recap for {self.file} using pre_model_wrapper (try {try_times}/5)...")

                try:
                    geminiWrapper = pre_model_wrapper(
                        system_instruction=self.category.review_system_prompt(),
                        schema=self._recap_schema(),
                        delete_files=True
                    )
                    model_responses = geminiWrapper.send_message(
                        user_prompt=user_prompt,
                        file_path=recap_source,
                        compress=False
                    )
                    recap_str = json_repair.loads(model_responses[0])["data"]
                    logger_config.info(f"Recap generated for {self.file} using pre_model_wrapper: {recap_str}")
                except Exception as e:
                    logger_config.error(f"Failed to generate recap using pre_model_wrapper: {e}")
                    try:
                        logger_config.info(f"Generating recap for {self.file} using AIStudioUIChat (try {try_times}/5)...")
                        cfg = BrowserConfig()
                        cfg.additionl_docker_flag = ' '.join(utils.get_docker_volume_mounts(cfg, self.file_parent_dir_path))
                        baseUIChat = AIStudioUIChat(cfg)
                        result = json_repair.loads(baseUIChat.quick_chat(
                            user_prompt=user_prompt,
                            system_prompt=self.category.review_system_prompt(),
                            file_path=os.path.basename(recap_source)
                        ))
                        if not isinstance(result, dict) or "data" not in result:
                            raise ValueError(f"AIStudioUIChat returned unexpected response for recap: {result!r}")
                        recap_str = result["data"]
                        logger_config.info(f"Recap generated for {self.file} using AIStudioUIChat: {recap_str}")
                    except Exception as e:
                        logger_config.error(f"Failed to generate recap for {self.file}: {e}")
                        recap_str = ""

            full_result["recap"] = recap_str

            if full_result["recap"] == "":
                raise Exception(f"Failed to generate recap for {self.file}")

            with open(self.recap_title_desc_path, "w", encoding="utf-8") as f:
                json.dump(full_result, f, indent=4, ensure_ascii=False)

        self._generate_title_and_description(full_result)
        return full_result

    def fix_spelling_mistakes(self):
        pass

    def generate_recap_audio(self):
        self.fix_spelling_mistakes()
        if utils.is_valid_audio(self.recap_audio_path):
            return self.recap_audio_path

        hf_tts_client = HFTTSClient()
        hf_tts_client.generate_audio_segment(self.generate_recap()["recap"], self.recap_audio_path)
        utils.copy(self.recap_audio_path, f"{self.recap_audio_path.replace('.wav', '_original.wav')}")
        utils.trim_silence(self.recap_audio_path)
        utils.speed_up_audio(self.recap_audio_path)

        if utils.is_valid_audio(self.recap_audio_path):
            return self.recap_audio_path
        else:
            raise Exception(f"Failed to generate recap audio for {self.file}")

    def _generate_sentences(self):
        if utils.is_valid_json(self.sentences_json_path):
            with open(self.sentences_json_path, "r") as f:
                data = json.load(f)
                if len(data) >= 5:
                    return data
                else:
                    logger_config.info(f"Sentences not valid (len {len(data)} < 5), regenerating...")
                    utils.remove_file(self.sentences_json_path)

        full_result = self.generate_recap()
        sentences = text_splitter.split(full_result["recap"])

        with open(self.sentences_json_path, "w", encoding="utf-8") as f:
            json.dump(sentences, f, indent=4, ensure_ascii=False)

        return sentences

    def _match_scene_schema(self):
        return genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["data"],
            properties = {
                "data": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["scene_caption", "recap_sentence"],
                        properties = {
                            "scene_caption": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "recap_sentence": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
            },
        )

    def _clip_animation_schema(self):
        return genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["clips"],
            properties = {
                "clips": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["clip_index", "animation", "transitionIn"],
                        properties = {
                            "clip_index": genai.types.Schema(type=genai.types.Type.INTEGER),
                            "animation": genai.types.Schema(type=genai.types.Type.STRING),
                            "transitionIn": genai.types.Schema(type=genai.types.Type.STRING),
                            "reasoning": genai.types.Schema(type=genai.types.Type.STRING),
                        },
                    ),
                ),
            },
        )

    def pick_clip_animations(self, clips_data, output_path=None):
        """Use LLM to assign per-clip animation and transition types."""
        if output_path is None:
            output_path = os.path.join(self.sentence_media_dir_path, "clip_animations.json")

        if utils.is_valid_json(output_path):
            with open(output_path, "r") as f:
                cached = json.load(f)
            if isinstance(cached, list) and len(cached) == len(clips_data):
                logger_config.info(f"clip_animations.json loaded ({len(cached)} clips), skipping LLM.")
                return cached

        with open(config.CLIP_ANIMATION_SYSTEM_PROMPT, "r") as f:
            system_prompt = f.read()

        user_prompt = json.dumps({
            "show_name": self.file_base_name_without_ext,
            "clips": [
                {
                    "clip_index": i,
                    "narration_text": c["narration_text"],
                    "duration_seconds": round(c["duration_seconds"], 2),
                    "words": c.get("words", []),
                }
                for i, c in enumerate(clips_data)
            ],
        }, ensure_ascii=False)

        parsed = None
        try_times = 0
        while try_times < 3 and parsed is None:
            try_times += 1
            try:
                geminiWrapper = pre_model_wrapper(
                    system_instruction=system_prompt,
                    schema=self._clip_animation_schema(),
                    delete_files=True
                )
                response = geminiWrapper.send_message(user_prompt=user_prompt)
                parsed = json_repair.loads(response[0])
            except Exception as e:
                logger_config.error(f"pick_clip_animations attempt {try_times} failed: {e}")

        if parsed is None or "clips" not in parsed:
            raise ValueError("Failed to get clip animations from LLM")

        animations = parsed["clips"]
        if len(animations) != len(clips_data):
            raise ValueError(f"Animation count mismatch: got {len(animations)}, expected {len(clips_data)}")

        with open(output_path, "w") as f:
            json.dump(animations, f, indent=4, ensure_ascii=False)

        logger_config.info(f"Clip animations: {[a.get('animation') for a in animations]}")
        return animations

    def _only_scene_caption_dialogue(self):
        data = self.generate_captions()
        return [
            {
                "scene_caption": obj["scene_caption"],
                "scene_dialogue": obj["scene_dialogue"]
            }
            for obj in data
        ]

    def match_scenes(self):
        match_scene = None
        sentences = self._generate_sentences()

        if utils.is_valid_json(self.match_scenes_online_path):
            with open(self.match_scenes_online_path, "r") as f:
                match_scene = json.load(f)
            try:
                all_recap = [sent["recap_sentence"] for sent in match_scene]
                all_recap[len(sentences) - 1]
            except:
                logger_config.info("Match scene not valid, regenerating...")
                utils.remove_file(self.match_scenes_online_path)
                match_scene = None

        retry_times = 0
        while match_scene is None and retry_times < 5:
            retry_times += 1
            user_prompt = f"""Scene Captions:: {self._only_scene_caption_dialogue()}\nRecap Sentences:: {sentences}"""

            with open(config.SCENE_MATCHING_SYSTEM_PROMPT, "r") as f:
                system_prompt = f.read()

            logger_config.info("Scene Matching")
            baseUIChat = AIStudioUIChat()
            match_scene = baseUIChat.quick_chat(
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )

            with open(config.JSON_VALIDATOR_SYSTEM_PROMPT, "r") as f:
                system_prompt = f.read()

            if not match_scene:
                raise ValueError("Failed to generate match scene")

            logger_config.info("JSON Validator")
            # Sanitize surrogate characters that can't be encoded to UTF-8.
            # Use surrogatepass→replace pattern which reliably strips lone surrogates.
            if isinstance(match_scene, str):
                match_scene = match_scene.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace')

            # Try direct JSON parse first (no AI needed)
            validated_scene = None
            try:
                validated_scene = utils.parse_json(match_scene, schema={
                    "type": list,
                    "items": {"required": ["scene_caption", "recap_sentence"]},
                })
            except Exception:
                pass

            if validated_scene is not None:
                match_scene = validated_scene
            else:
                try:
                    # Fall back to AI JSON validation
                    geminiWrapper = pre_model_wrapper(
                        system_instruction=system_prompt,
                        schema=self._match_scene_schema(),
                        delete_files=True
                    )
                    model_responses = geminiWrapper.send_message(
                        user_prompt=match_scene
                    )
                    match_scene = json_repair.loads(model_responses[0])["data"]
                    all_recap = [sent["recap_sentence"] for sent in match_scene]
                    all_recap[len(sentences) - 1]
                except Exception as e:
                    logger_config.error(f"Sentence not similar retry: {e}")
                    match_scene = None

        if match_scene is None:
            raise ValueError("Failed to generate match scene")

        if retry_times > 0:
            with open(self.match_scenes_online_path, "w", encoding="utf-8") as f:
                json.dump(match_scene, f, indent=4, ensure_ascii=False)

        return match_scene

    def choose_best_frames(self):
        best_frames = None
        if utils.is_valid_json(self.choose_best_frames_json_path):
            with open(self.choose_best_frames_json_path, "r") as f:
                best_frames = json.load(f)
                if len(best_frames) > 0:
                    return best_frames

        with sentence_matcher.TextFrameAligner(
            cache_path=self.sentence_frames_dir_path
        ) as aligner:
            best_frames = aligner.match_scenes_online(
                self._generate_sentences(),
                self.generate_captions(),
                self.match_scenes()
            )

        with open(self.choose_best_frames_json_path, "w", encoding="utf-8") as f:
            json.dump(best_frames, f, indent=4, ensure_ascii=False)

        if len(best_frames) > 0:
            return best_frames
        else:
            raise Exception(f"Failed to generate best frames for {self.file}")

    def choose_emojis(self):
        best_frames_with_emotion = self.choose_best_frames()
        with open(config.KEYWORD_EXTRACT_SYSTEM_PROMPT, "r") as file:
            system_prompt = file.read()

        hf_ttt_client = HFTTTClient()
        for i, frame_obj in enumerate(best_frames_with_emotion):
            logger_config.info(f"Working on TTT frame {i+1} of {len(best_frames_with_emotion)}", overwrite=True)
            updated = False
            if "critical_word" not in frame_obj:
                model_response = json_repair.loads(hf_ttt_client.generate(
                    text=f'The sentence:: {frame_obj["recap_sentence"]}',
                    system_prompt=system_prompt
                ))
                if not isinstance(model_response, dict):
                    raise ValueError(f"HFTTTClient returned unexpected response for emoji: {model_response!r}")
                frame_obj["critical_word"] = model_response.get("word", "")
                frame_obj["critical_emoji"] = model_response.get("emoji", "")
                updated = True

            if updated:
                with open(self.choose_best_frames_json_path, "w") as f:
                    json.dump(best_frames_with_emotion, f, indent=4, ensure_ascii=False)

        return best_frames_with_emotion

    def create_clip_for_frames(self):
        best_frames_with_emotion = self.choose_emojis()
        hf_tts_client = HFTTSClient()
        hf_stt_client = HFSTTClient()

        for i, frame_obj in enumerate(best_frames_with_emotion):
            logger_config.info(f"Working on clip frame {i+1} of {len(best_frames_with_emotion)}", overwrite=True)
            updated = False
            audio_path = os.path.join(self.sentence_media_dir_path, f"audio_{i}.wav")
            video_path = os.path.join(self.sentence_media_dir_path, f"video_{i}.mp4")

            if "audio_path" not in frame_obj or not utils.is_valid_audio(audio_path):
                if utils.file_exists(audio_path):
                    utils.remove_file(audio_path)

                hf_tts_client.generate_audio_segment(frame_obj["recap_sentence"], audio_path)
                utils.copy(audio_path, f"{audio_path.replace('.wav', '_original.wav')}")
                utils.trim_silence(audio_path)
                utils.speed_up_audio(audio_path)
                frame_obj["audio_path"] = audio_path
                updated = True

            if "transcription" not in frame_obj:
                transcription_path = hf_stt_client.transcribe(audio_path)
                with open(transcription_path, "r") as f:
                    transcription = json.load(f)
                    transcription = transcription["segments"]["word"]
                frame_obj["transcription"] = transcription
                updated = True

            if "duration" not in frame_obj:
                audio_duration_result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                    capture_output=True, text=True, check=True
                )
                frame_obj["duration"] = float(audio_duration_result.stdout.strip())
                updated = True

            if "frame_clip_path" not in frame_obj or not utils.is_valid_video(video_path):
                if utils.file_exists(video_path):
                    utils.remove_file(video_path)

                side_dur = float(frame_obj["duration"]) / 2
                clip_start = float(frame_obj["frame_second"]) - side_dur
                clip_duration = side_dur * 2
                # Re-encode clip with fixed fps/timestamps so duration matches downstream outputs.
                utils.encode_video_consistent(
                    input_path=self.file,
                    output_path=video_path,
                    start_time=clip_start,
                    duration=clip_duration,
                    fps=24,
                    crf=18,
                    preset="fast",
                    include_audio=False
                )
                frame_obj["frame_clip_path"] = video_path
                updated = True

            if updated:
                with open(self.choose_best_frames_json_path, "w") as f:
                    json.dump(best_frames_with_emotion, f, indent=4, ensure_ascii=False)

        return best_frames_with_emotion

    def _set_face_tagger(self):
        cwd = "/tmp/FaceTagger"
        if not utils.dir_exists(cwd):
            utils.setup_git_repo_get_install_pip(
                repo_url="https://github.com/jebin2/FaceTagger.git",
                target_path=cwd,
                pip_name="FaceTagger",
                requirements_file="requirements_auto_crop.txt"
            )
            if not utils.dir_exists(cwd):
                raise ValueError("FaceTagger not setup correctly.")

        return cwd, os.path.expanduser("~/.pyenv/versions/FaceTagger_env/bin/python")

    def _add_emoji_to_clip(self, best_frames_with_focus_character):
        for i, frame_obj in enumerate(best_frames_with_focus_character):
            logger_config.info(f"Working on emoji frame {i+1} of {len(best_frames_with_focus_character)}", overwrite=True)
            updated = False
            new_path = os.path.join(os.path.dirname(frame_obj["auto_crop_9x16_path"]), "emoji_added_" + os.path.basename(frame_obj["auto_crop_9x16_path"]))
            if "emoji_added_path" not in frame_obj or not utils.is_valid_video(new_path):
                if utils.file_exists(new_path):
                    utils.remove_file(new_path)

                emoji_placer.place_emoji_on_video(
                    video_path=frame_obj["auto_crop_9x16_path"],
                    img_path=utils.to_abs(frame_obj["frame_path"], config.CONTENT_TO_BE_PROCESSED),
                    emoji_text=frame_obj["critical_emoji"],
                    output_path=new_path
                )

                frame_obj["emoji_added_path"] = new_path
                updated = True

            if updated:
                with open(self.choose_best_frames_json_path, "w") as f:
                    json.dump(best_frames_with_focus_character, f, indent=4, ensure_ascii=False)

        return best_frames_with_focus_character

    def focus_characters_clip(self):
        cwd, python_path = self._set_face_tagger()
        best_frames_with_focus_character = self.create_clip_for_frames()

        for i, frame_obj in enumerate(best_frames_with_focus_character):
            logger_config.info(f"Working on char frame {i+1} of {len(best_frames_with_focus_character)}", overwrite=True)
            updated = False
            new_path = os.path.join(os.path.dirname(frame_obj["frame_clip_path"]), "auto_crop_9x16_" + os.path.basename(frame_obj["frame_clip_path"]))
            if "auto_crop_9x16_path" not in frame_obj or not utils.is_valid_video(new_path):
                if utils.file_exists(new_path):
                    utils.remove_file(new_path)

                cmd = f"{python_path} auto_crop_9x16.py '{utils.to_abs(frame_obj['frame_clip_path'], config.CONTENT_TO_BE_PROCESSED)}' {'anime' if self.category == config.ANIME else 'real'}"
                subprocess.run(
                    ["bash", "-c", cmd],
                    cwd=cwd,
                    text=True,
                    check=True,
                    env=config.SUBPROCESS_ENV
                )

                utils.copy(f"{cwd}/output_from_auto_crop_9x16.mp4", new_path)
                frame_obj["auto_crop_9x16_path"] = new_path
                updated = True

            if updated:
                with open(self.choose_best_frames_json_path, "w") as f:
                    json.dump(best_frames_with_focus_character, f, indent=4, ensure_ascii=False)

        # self._add_emoji_to_clip(best_frames_with_focus_character)
        return best_frames_with_focus_character

    def create_bg_music(self):
        if utils.is_valid_audio(self.musicgen_path):
            return self.musicgen_path

        result = subprocess.run(
            [
                sys.executable,
                "-m", "music_creator.core",
                self.generate_recap()["recap"],
                self.musicgen_path
            ],
            cwd=config.BASE_PATH,
            env=config.SUBPROCESS_ENV,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"music_creator.core failed (exit {result.returncode}):\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        utils.manage_gpu(action="clear_cache")

        if utils.is_valid_audio(self.musicgen_path):
            return self.musicgen_path
        else:
            raise Exception(f"Failed to generate music for {self.file}")

    def merge_audio(self):
        return self.generate_recap_audio() # currently ausio not working so.
        if utils.is_valid_audio(self.merged_audio_path):
            return self.merged_audio_path

        recap_audio = self.generate_recap_audio()
        bg_music = self.create_bg_music()
        merge_music.process(
            audio_path_1=recap_audio,
            audio_path_2=bg_music,
            output_path=self.merged_audio_path
        )

        if utils.is_valid_audio(self.merged_audio_path):
            return self.merged_audio_path
        else:
            raise Exception(f"Failed to merge audio for {self.file}")

    def create_final_video(self):
        if utils.is_valid_video(self.final_video_path):
            return self.final_video_path

        best_frames_with_focus_character = self.focus_characters_clip()
        merged_audio_path = self.merge_audio()

        concat_list_path = self.final_video_path + ".concat.txt"
        with open(concat_list_path, "w") as f:
            for frame_obj in best_frames_with_focus_character:
                f.write(f"file '{utils.to_abs(frame_obj['emoji_added_path'], config.CONTENT_TO_BE_PROCESSED)}'\n")

        utils.run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", utils.to_abs(concat_list_path, config.CONTENT_TO_BE_PROCESSED),
            "-i", utils.to_abs(merged_audio_path, config.CONTENT_TO_BE_PROCESSED),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-vf", "fps=24",
            "-c:a", "aac",
            "-shortest",
            utils.to_abs(self.final_video_path, config.CONTENT_TO_BE_PROCESSED)
        ])
        os.remove(concat_list_path)

        if utils.is_valid_video(self.final_video_path):
            normalize_loudness(self.final_video_path)
            ffmpeg_optimise.convert_and_compare(self.final_video_path, f"/tmp/{self.file_base_name_without_ext}.hevc.mp4", overwrite_original=True)
            return self.final_video_path
        else:
            raise Exception(f"Failed to generate final video for {self.file}")

    # ------------------------------------------------------------------ remotion

    def generate_remotion_manifest(self, best_frames_with_focus_character):
        """Build a ReelManifest JSON for remotion-reels from the pipeline output."""
        full_result = self.generate_recap()
        title = full_result.get("youtube_title", self.file_base_name_without_ext)

        # Build input for LLM animation picker
        clips_data = [
            {
                "narration_text": frame_obj.get("recap_sentence", ""),
                "duration_seconds": float(frame_obj["duration"]),
                "words": frame_obj.get("transcription", []),
            }
            for frame_obj in best_frames_with_focus_character
        ]
        animations = self.pick_clip_animations(clips_data)
        anim_by_index = {a["clip_index"]: a for a in animations}
        transition_by_index = {a["clip_index"]: a.get("transitionIn", "none") for a in animations}

        clips = []
        for i, frame_obj in enumerate(best_frames_with_focus_character):
            video_abs = utils.to_abs(frame_obj["auto_crop_9x16_path"], config.CONTENT_TO_BE_PROCESSED)
            audio_abs = utils.to_abs(frame_obj["audio_path"], config.CONTENT_TO_BE_PROCESSED)
            video_rel = "render_assets/" + os.path.relpath(video_abs, config.CONTENT_TO_BE_PROCESSED)
            audio_rel = "render_assets/" + os.path.relpath(audio_abs, config.CONTENT_TO_BE_PROCESSED)
            anim_info = anim_by_index.get(i, {})

            next_transition_in = transition_by_index.get(i + 1, "none") if (i + 1) < len(best_frames_with_focus_character) else "none"
            current_transition_in = transition_by_index.get(i, "none")
            clip_duration = float(frame_obj["duration"])
            if next_transition_in != "none":
                clip_duration += config.TRANSITION_DURATION
            if i > 0 and current_transition_in != "none":
                clip_duration = max(clip_duration, config.TRANSITION_DURATION)

            clip = {
                "videoSrc": video_rel,
                "audioSrc": audio_rel,
                "durationInSeconds": clip_duration,
                "animation": anim_info.get("animation", "ken_burns"),
                "transitionIn": anim_info.get("transitionIn", "none"),
                "wordTimings": frame_obj.get("transcription", []),
            }
            # emoji = frame_obj.get("critical_emoji", "")
            # if emoji:
            #     clip["emojiText"] = emoji

            clips.append(clip)

        manifest = {
            "fps": 24,
            "width": 1080,
            "height": 1920,
            "title": title,
            "clips": clips,
        }

        manifest_path = os.path.join(self.sentence_media_dir_path, "reels_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"manifest": manifest}, f, indent=4, ensure_ascii=False)

        logger_config.info(f"Reel manifest written: {manifest_path} ({len(clips)} clips)")
        return manifest_path

    def _ensure_remotion_reels_ready(self, remotion_dir):
        node_modules = os.path.join(remotion_dir, "node_modules")
        if not os.path.isdir(node_modules):
            logger_config.info("Installing remotion-reels npm dependencies...")
            result = subprocess.run(["npm", "install"], cwd=remotion_dir, capture_output=False)
            if result.returncode != 0:
                raise RuntimeError("npm install failed for remotion-reels")
            logger_config.info("npm install complete.")

    def create_final_video_remotion(self):
        """Render the final reel using Remotion instead of raw FFmpeg concat."""
        if utils.is_valid_video(self.final_video_path):
            return self.final_video_path

        best_frames_with_focus_character = self.focus_characters_clip()
        manifest_path = self.generate_remotion_manifest(best_frames_with_focus_character)

        remotion_dir = os.path.join(config.BASE_PATH, "remotion-reels")
        self._ensure_remotion_reels_ready(remotion_dir)

        # Symlink render_assets -> BASE_PATH so staticFile("render_assets/...") resolves
        public_dir = os.path.join(remotion_dir, "public")
        os.makedirs(public_dir, exist_ok=True)
        render_link = os.path.join(public_dir, "render_assets")
        if os.path.islink(render_link):
            os.unlink(render_link)
        os.symlink(config.CONTENT_TO_BE_PROCESSED, render_link)
        logger_config.info(f"Symlinked render_assets -> {config.CONTENT_TO_BE_PROCESSED}")

        output_abs = utils.to_abs(self.final_video_path, config.CONTENT_TO_BE_PROCESSED)
        manifest_abs = utils.to_abs(manifest_path, config.CONTENT_TO_BE_PROCESSED)

        cmd = [
            "npx", "remotion", "render", "ReelVideo",
            "--props", manifest_abs,
            "--output", output_abs,
            "--codec", "h264",
            "--log", "verbose",
        ]

        logger_config.info(f"Running Remotion: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, cwd=remotion_dir, capture_output=False)
        finally:
            if os.path.islink(render_link):
                os.unlink(render_link)
                logger_config.info("Cleaned up render_assets symlink.")

        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed with exit code {result.returncode}")

        if utils.is_valid_video(self.final_video_path):
            normalize_loudness(self.final_video_path)
            ffmpeg_optimise.convert_and_compare(self.final_video_path, f"/tmp/{self.file_base_name_without_ext}.hevc.mp4", overwrite_original=True)
            return self.final_video_path
        else:
            raise Exception(f"Remotion render produced no valid video for {self.file}")

    # ------------------------------------------------------------------ long-form

    def generate_long_recap(self):
        full_result = {}
        if utils.is_valid_json(self.long_recap_path):
            with open(self.long_recap_path, "r") as f:
                full_result = json.load(f)

        if full_result.get("recap", "") == "":
            recap_source = self.category.get_recap_source_file() or self.get_compressed_file()
            if recap_source != self.get_compressed_file():
                logger_config.info(f"Using transcript file for long recap: {recap_source}")

            user_prompt = self.file_base_name_with_ext
            recap_str = ""
            try_times = 0
            while try_times < 5 and recap_str == "":
                try_times += 1
                logger_config.info(f"Generating long recap for {self.file} (try {try_times}/5)...")
                try:
                    geminiWrapper = pre_model_wrapper(
                        system_instruction=self.category.long_recap_system_prompt(),
                        schema=self._recap_schema(),
                        delete_files=True
                    )
                    model_responses = geminiWrapper.send_message(
                        user_prompt=user_prompt,
                        file_path=recap_source,
                        compress=False
                    )
                    recap_str = json_repair.loads(model_responses[0])["data"]
                    logger_config.info(f"Long recap generated for {self.file}: {recap_str[:100]}...")
                except Exception as e:
                    logger_config.error(f"Failed to generate long recap: {e}")
                    recap_str = ""

            full_result["recap"] = recap_str
            if full_result["recap"] == "":
                raise Exception(f"Failed to generate long recap for {self.file}")

            with open(self.long_recap_path, "w", encoding="utf-8") as f:
                json.dump(full_result, f, indent=4, ensure_ascii=False)

        return full_result

    def generate_longform_manifest(self, best_frames):
        title = self.generate_recap().get("youtube_title", self.file_base_name_without_ext)

        clips_data = [
            {
                "narration_text": frame_obj.get("recap_sentence", ""),
                "duration_seconds": float(frame_obj["duration"]),
                "words": frame_obj.get("transcription", []),
            }
            for frame_obj in best_frames
        ]

        longform_animations_path = os.path.join(self.longform_media_dir_path, "clip_animations.json")
        animations = self.pick_clip_animations(clips_data, output_path=longform_animations_path)
        anim_by_index = {a["clip_index"]: a for a in animations}
        transition_by_index = {a["clip_index"]: a.get("transitionIn", "none") for a in animations}

        clips = []
        for i, frame_obj in enumerate(best_frames):
            frame_abs = utils.to_abs(frame_obj["frame_path"], config.CONTENT_TO_BE_PROCESSED)
            audio_abs = utils.to_abs(frame_obj["audio_path"], config.CONTENT_TO_BE_PROCESSED)
            frame_rel = "render_assets/" + os.path.relpath(frame_abs, config.CONTENT_TO_BE_PROCESSED)
            audio_rel = "render_assets/" + os.path.relpath(audio_abs, config.CONTENT_TO_BE_PROCESSED)
            anim_info = anim_by_index.get(i, {})

            next_transition = transition_by_index.get(i + 1, "none") if (i + 1) < len(best_frames) else "none"
            current_transition = transition_by_index.get(i, "none")
            clip_duration = float(frame_obj["duration"])
            if next_transition != "none":
                clip_duration += config.TRANSITION_DURATION
            if i > 0 and current_transition != "none":
                clip_duration = max(clip_duration, config.TRANSITION_DURATION)

            clips.append({
                "imageSrc": frame_rel,
                "audioSrc": audio_rel,
                "durationInSeconds": clip_duration,
                "animation": anim_info.get("animation", "ken_burns"),
                "transitionIn": anim_info.get("transitionIn", "none"),
                "wordTimings": frame_obj.get("transcription", []),
            })

        manifest = {
            "fps": 24,
            "width": 1920,
            "height": 1080,
            "title": title,
            "clips": clips,
        }

        manifest_path = os.path.join(self.longform_media_dir_path, "longform_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"manifest": manifest}, f, indent=4, ensure_ascii=False)

        logger_config.info(f"Long-form manifest written: {manifest_path} ({len(clips)} clips)")
        return manifest_path

    def _generate_longform_sentences(self):
        if utils.is_valid_json(self.longform_sentences_json_path):
            with open(self.longform_sentences_json_path, "r") as f:
                data = json.load(f)
                if len(data) >= 5:
                    return data
                else:
                    logger_config.info(f"Longform sentences not valid (len {len(data)} < 5), regenerating...")
                    utils.remove_file(self.longform_sentences_json_path)

        full_result = self.generate_long_recap()
        sentences = text_splitter.split(full_result["recap"])

        with open(self.longform_sentences_json_path, "w", encoding="utf-8") as f:
            json.dump(sentences, f, indent=4, ensure_ascii=False)

        return sentences

    def match_longform_scenes(self):
        match_scene = None
        sentences = self._generate_longform_sentences()

        if utils.is_valid_json(self.longform_match_scenes_path):
            with open(self.longform_match_scenes_path, "r") as f:
                match_scene = json.load(f)
            try:
                all_recap = [sent["recap_sentence"] for sent in match_scene]
                all_recap[len(sentences) - 1]
            except:
                logger_config.info("Longform match scene not valid, regenerating...")
                utils.remove_file(self.longform_match_scenes_path)
                match_scene = None

        retry_times = 0
        while match_scene is None and retry_times < 5:
            retry_times += 1
            user_prompt = f"""Scene Captions:: {self._only_scene_caption_dialogue()}\nRecap Sentences:: {sentences}"""

            with open(config.SCENE_MATCHING_SYSTEM_PROMPT, "r") as f:
                system_prompt = f.read()

            logger_config.info("Longform Scene Matching")
            baseUIChat = AIStudioUIChat()
            match_scene = baseUIChat.quick_chat(
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )

            with open(config.JSON_VALIDATOR_SYSTEM_PROMPT, "r") as f:
                system_prompt = f.read()

            if not match_scene:
                raise ValueError("Failed to generate longform match scene")

            logger_config.info("JSON Validator")
            if isinstance(match_scene, str):
                match_scene = match_scene.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace')

            validated_scene = None
            try:
                validated_scene = utils.parse_json(match_scene, schema={
                    "type": list,
                    "items": {"required": ["scene_caption", "recap_sentence"]},
                })
            except Exception:
                pass

            if validated_scene is not None:
                match_scene = validated_scene
            else:
                try:
                    geminiWrapper = pre_model_wrapper(
                        system_instruction=system_prompt,
                        schema=self._match_scene_schema(),
                        delete_files=True
                    )
                    model_responses = geminiWrapper.send_message(
                        user_prompt=match_scene
                    )
                    match_scene = json_repair.loads(model_responses[0])["data"]
                    all_recap = [sent["recap_sentence"] for sent in match_scene]
                    all_recap[len(sentences) - 1]
                except Exception as e:
                    logger_config.error(f"Longform sentence not similar retry: {e}")
                    match_scene = None

        if match_scene is None:
            raise ValueError("Failed to generate longform match scene")

        if retry_times > 0:
            with open(self.longform_match_scenes_path, "w", encoding="utf-8") as f:
                json.dump(match_scene, f, indent=4, ensure_ascii=False)

        return match_scene

    def choose_longform_best_frames(self):
        best_frames = None
        if utils.is_valid_json(self.longform_best_frames_json_path):
            with open(self.longform_best_frames_json_path, "r") as f:
                best_frames = json.load(f)
                if len(best_frames) > 0:
                    return best_frames

        with sentence_matcher.TextFrameAligner(
            cache_path=self.longform_sentence_frames_dir_path
        ) as aligner:
            best_frames = aligner.match_scenes_online(
                self._generate_longform_sentences(),
                self.generate_captions(),
                self.match_longform_scenes()
            )

        with open(self.longform_best_frames_json_path, "w", encoding="utf-8") as f:
            json.dump(best_frames, f, indent=4, ensure_ascii=False)

        if len(best_frames) > 0:
            return best_frames
        else:
            raise Exception(f"Failed to generate longform best frames for {self.file}")

    def create_clip_for_longform_frames(self):
        best_frames = self.choose_longform_best_frames()
        hf_tts_client = HFTTSClient()
        hf_stt_client = HFSTTClient()

        for i, frame_obj in enumerate(best_frames):
            logger_config.info(f"Working on longform clip frame {i+1} of {len(best_frames)}", overwrite=True)
            updated = False
            audio_path = os.path.join(self.longform_media_dir_path, f"audio_{i}.wav")

            if "audio_path" not in frame_obj or not utils.is_valid_audio(audio_path):
                if utils.file_exists(audio_path):
                    utils.remove_file(audio_path)

                hf_tts_client.generate_audio_segment(frame_obj["recap_sentence"], audio_path)
                utils.copy(audio_path, f"{audio_path.replace('.wav', '_original.wav')}")
                utils.trim_silence(audio_path)
                utils.speed_up_audio(audio_path)
                frame_obj["audio_path"] = audio_path
                updated = True

            if "transcription" not in frame_obj:
                transcription_path = hf_stt_client.transcribe(audio_path)
                with open(transcription_path, "r") as f:
                    transcription = json.load(f)
                    transcription = transcription["segments"]["word"]
                frame_obj["transcription"] = transcription
                updated = True

            if "duration" not in frame_obj:
                audio_duration_result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                    capture_output=True, text=True, check=True
                )
                frame_obj["duration"] = float(audio_duration_result.stdout.strip())
                updated = True

            if updated:
                with open(self.longform_best_frames_json_path, "w") as f:
                    json.dump(best_frames, f, indent=4, ensure_ascii=False)

        return best_frames

    def create_longform_video_remotion(self):
        if utils.is_valid_video(self.longform_video_path):
            return self.longform_video_path

        best_frames = self.create_clip_for_longform_frames()
        manifest_path = self.generate_longform_manifest(best_frames)

        remotion_dir = os.path.join(config.BASE_PATH, "remotion-reels")
        self._ensure_remotion_reels_ready(remotion_dir)

        public_dir = os.path.join(remotion_dir, "public")
        os.makedirs(public_dir, exist_ok=True)
        render_link = os.path.join(public_dir, "render_assets")
        if os.path.islink(render_link):
            os.unlink(render_link)
        os.symlink(config.CONTENT_TO_BE_PROCESSED, render_link)
        logger_config.info(f"Symlinked render_assets -> {config.CONTENT_TO_BE_PROCESSED}")

        output_abs = utils.to_abs(self.longform_video_path, config.CONTENT_TO_BE_PROCESSED)
        manifest_abs = utils.to_abs(manifest_path, config.CONTENT_TO_BE_PROCESSED)

        cmd = [
            "npx", "remotion", "render", "ReelVideo",
            "--props", manifest_abs,
            "--output", output_abs,
            "--codec", "h264",
            "--log", "verbose",
        ]

        logger_config.info(f"Running Remotion for long-form: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, cwd=remotion_dir, capture_output=False)
        finally:
            if os.path.islink(render_link):
                os.unlink(render_link)
                logger_config.info("Cleaned up render_assets symlink.")

        if result.returncode != 0:
            raise RuntimeError(f"Remotion long-form render failed with exit code {result.returncode}")

        if utils.is_valid_video(self.longform_video_path):
            normalize_loudness(self.longform_video_path)
            ffmpeg_optimise.convert_and_compare(self.longform_video_path, f"/tmp/{self.file_base_name_without_ext}_longform.hevc.mp4", overwrite_original=True)
            return self.longform_video_path
        else:
            raise Exception(f"Remotion long-form render produced no valid video for {self.file}")

    # ------------------------------------------------------------------ main

    def process(self):
        if self.is_processed():
            logger_config.info(f"Already processed: {self.file}")
            return

        self.generate_long_recap()
        self.create_final_video_remotion()
        self.create_longform_video_remotion()
        self.category.create_progress_file()
