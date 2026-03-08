import os
from custom_logger import logger_config
from youtube_auto_pub import YouTubeConfig, YouTubeUploader, VideoMetadata
from .. import config as project_config

def _get_youtube_config(token_filename, client_secret_filename):
    """Create YouTubeConfig from environment variables."""
    encryption_key = os.getenv("CC_ENCRYPT_KEY", "") or os.getenv("ENCRYPT_KEY", "")
    encrypt_path = os.path.join(project_config.TEMP_PATH, "yt_creds")
    authorization_code_path = os.path.join(project_config.TEMP_PATH, "authorization_code.txt")
    browser_executable = os.getenv("BROWSER_EXECUTABLE")
    os.makedirs(encrypt_path, exist_ok=True)
    return YouTubeConfig(
        encrypt_path=encrypt_path,
        authorization_code_path=authorization_code_path,
        browser_executable=browser_executable,
        is_docker=False,
        has_display=True,
        headless_mode=False,
        docker_name="cc_youtube_auto_pub",
        encryption_key=encryption_key.encode() if encryption_key else None,
        hf_repo_id=os.getenv("HF_YT_CRED_REPO_ID"),
        hf_token=os.getenv("HF_TOKEN"),
        hf_repo_type="dataset",
        google_email=os.getenv("GOOGLE_EMAIL"),
        google_password=os.getenv("GOOGLE_PASSWORD"),
        token_filename=token_filename,
        client_secret_filename=client_secret_filename,
    )

class YoutubePublisher:
    def __init__(self, publisher_processor):
        self.pp = publisher_processor

    def get_service(self, token_filename, client_secret_filename):
        cache_key = token_filename
        service = self.pp.get_service(cache_key)
        if service:
            logger_config.debug(f"Using cached YouTube service for: {cache_key}")
            return service, None

        cfg = _get_youtube_config(token_filename, client_secret_filename)
        uploader = YouTubeUploader(cfg)
        service = uploader.get_service(cache_key=cache_key)

        if service:
            self.pp.set_service(cache_key, service)
            logger_config.success(f"YouTube service built for: {cache_key}")

        return service, uploader

    def publish(self, progress, final_video_path):
        credential_name = progress.get("CREDENTIAL_NAME")
        token_name = progress.get("TOKEN_NAME")
        title = progress.get("YOUTUBE_TITLE", "watch now")

        if not credential_name or not token_name:
            logger_config.warning("Missing YouTube credentials in progress file, skipping.")
            return False

        service, uploader = self.get_service(token_name, credential_name)
        if not service:
            logger_config.error("Failed to get YouTube service.")
            return False

        if not uploader:
            # Rebuild uploader in case service was pulled from cache
            cfg = _get_youtube_config(token_name, credential_name)
            uploader = YouTubeUploader(cfg)

        description = self.pp.category.get_yt_description(title)
        tags = self.pp.category.get_yt_tags()

        metadata = VideoMetadata(
            title=title[:100],
            description=description,
            tags=tags,
            category_id="24",  # Entertainment
            privacy_status="private",
            made_for_kids=False,
        )

        video_id = uploader.upload_video(
            service=service,
            video_path=final_video_path,
            metadata=metadata,
        )

        if video_id:
            logger_config.success(f"Video uploaded to YouTube with ID: {video_id}")
            return True

        logger_config.error(f"Failed to upload video: {final_video_path}")
        return False
