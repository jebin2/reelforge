from .. import common
from custom_logger import logger_config
import torch
from sentence_transformers import SentenceTransformer, util
import os
import json
import gc
import shutil

TEMP_DIR = os.path.abspath("temp_dir")

class TextFrameAligner:
    def __init__(self, cache_path, sentence_model_name='all-mpnet-base-v2'):
        self.sentence_model_name = sentence_model_name
        self.embedder = None
        self.cache_path = cache_path

    @torch.inference_mode()
    def load_sentence_transformer(self):
        if self.embedder is not None:
            return
        logger_config.info("Loading SentenceTransformer")
        self.embedder = SentenceTransformer(self.sentence_model_name, device=common.get_device())
        logger_config.info("SentenceTransformer loaded successfully")

    def unload_sentence_transformer(self):
        if self.embedder:
            logger_config.info("Unloading SentenceTransformer model")
            del self.embedder
            common.manage_gpu("clear_cache")

    def match_scenes_online(self, sentences, extract_scenes_json, match_scene):
        self.load_sentence_transformer()
        only_captions = [obj["scene_caption"] for obj in extract_scenes_json]
        captions_embeddings = self.embedder.encode(only_captions, convert_to_tensor=True)

        resulted_sentence = [sent["recap_sentence"] for sent in match_scene]
        resulted_sentences_embeddings = self.embedder.encode(resulted_sentence, convert_to_tensor=True)

        result = []
        max_sentences_len = max([len(sent) for sent in sentences]) + 20
        for i, curr_sent in enumerate(sentences):
            query_embedding = self.embedder.encode(curr_sent, convert_to_tensor=True)
            similarities = util.cos_sim(query_embedding, resulted_sentences_embeddings)
            resulted_idx = similarities.argmax()

            scene_caption = match_scene[resulted_idx]["scene_caption"]
            recap_sentence =  match_scene[resulted_idx]["recap_sentence"]
            if len(scene_caption) < len(recap_sentence):
                scene_caption =  match_scene[resulted_idx]["recap_sentence"]
                recap_sentence =  match_scene[resulted_idx]["scene_caption"]

            if len(recap_sentence) > max_sentences_len:
                os.remove(cache_dir)
                raise ValueError(f"Invalid sentence:: {recap_sentence}")

            query_embedding = self.embedder.encode(scene_caption, convert_to_tensor=True)
            similarities = util.cos_sim(query_embedding, captions_embeddings)
            frame_idx = similarities.argmax()

            frame_path = extract_scenes_json[frame_idx]["frame_path"][0]

            count = sum(1 for item in result if item["frame_path"] == frame_path)

            if count < 4:
                result.append({
                    "recap_sentence": curr_sent,
                    "frame_second": extract_scenes_json[frame_idx]["best_time"],
                    "frame_path": frame_path,
                    "scene_caption": extract_scenes_json[frame_idx]["scene_caption"],
                })
            else:
                shutil.copy2(cache_dir, cache_dir.replace(".json", ".json.bk"))
                os.remove(cache_dir)
                raise ValueError(f"duplicate frame:: {frame_path}")

            # Save frame
            output_path = os.path.join(self.cache_path, f"sentence_{i:02d}_frame_{frame_idx}.jpg")
            shutil.copy2(extract_scenes_json[frame_idx]["frame_path"][0], output_path)

            # Log progress
            logger_config.info(f"Aligned {i+1}/{len(sentences)} sentences")

        self.unload_sentence_transformer()
        return result

    def cleanup(self):
        try:
            if hasattr(self, 'embedder') and self.embedder is not None:
                self.embedder = None
                print("embedder reference cleared.")

            gc.collect()

            try:
                if common.is_gpu_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                    print("CUDA memory cleaned.")
            except ImportError:
                print("Torch not available; skipped GPU cleanup.")

            print("Cleanup completed successfully.")
            common.manage_gpu(action="clear_cache")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __del__(self):
        self.cleanup()
