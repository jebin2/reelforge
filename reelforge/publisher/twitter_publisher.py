import os
import json
from requests_oauthlib import OAuth1Session
from custom_logger import logger_config

TWEET_V2_URL = "https://api.twitter.com/2/tweets"

class TwitterPublisher:
    def __init__(self, publisher_processor):
        self.pp = publisher_processor

    def get_service(self):
        cache_key = f"twitter_{self.pp.category}"
        service = self.pp.get_service(cache_key)
        if service:
            logger_config.debug(f"Using cached twitter service for: {cache_key}")
            return service

        progress = self.pp._get_progress()
        credential_name = progress.get("TWITTER_CREDENTIAL_NAME")
        token_name = progress.get("TWITTER_TOKEN_NAME")

        if not credential_name or not token_name:
            logger_config.warning("Missing Twitter credentials in progress file.")
            return None

        with open(credential_name, 'r') as f:
            credentials = json.load(f)
        consumer_key = credentials['api_key']
        consumer_secret = credentials['api_secret_key']

        access_token = None
        access_token_secret = None

        try:
            if os.path.exists(token_name):
                with open(token_name, 'r') as f:
                    tokens = json.load(f)
                access_token = tokens['access_token']
                access_token_secret = tokens['access_token_secret']
                logger_config.success("Twitter access tokens loaded from file.")
        except Exception as e:
            logger_config.error(f"Error loading twitter tokens: {e}")
            access_token = None
            access_token_secret = None

        if not access_token or not access_token_secret:
            request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
            oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

            try:
                fetch_response = oauth.fetch_request_token(request_token_url)
            except ValueError:
                logger_config.error("Error fetching twitter request token. Check consumer_key or consumer_secret.")
                return None

            resource_owner_key = fetch_response.get("oauth_token")
            resource_owner_secret = fetch_response.get("oauth_token_secret")

            base_authorization_url = "https://api.twitter.com/oauth/authorize"
            authorization_url = oauth.authorization_url(base_authorization_url)
            logger_config.info(f"Please go here and authorize: {authorization_url}")
            verifier = input("Paste the PIN here: ")

            oauth = OAuth1Session(
                consumer_key,
                client_secret=consumer_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=verifier,
            )
            oauth_tokens = oauth.fetch_access_token("https://api.twitter.com/oauth/access_token")
            access_token = oauth_tokens["oauth_token"]
            access_token_secret = oauth_tokens["oauth_token_secret"]

            with open(token_name, 'w') as f:
                json.dump({'access_token': access_token, 'access_token_secret': access_token_secret}, f)
            logger_config.success("Twitter access tokens saved.")

        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        self.pp.set_service(cache_key, oauth)
        return oauth

    def upload_image(self, image_path):
        media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        with open(image_path, 'rb') as f:
            response = self.get_service().post(media_upload_url, files={"media": f})

        if response.status_code != 200:
            logger_config.error(f"Twitter image upload failed: {response.status_code} {response.text}")
            return None

        media_id = response.json()['media_id_string']
        logger_config.success(f"Twitter image uploaded, media ID: {media_id}")
        return media_id

    def upload_video(self, video_path):
        """Chunked video upload to Twitter."""
        media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        service = self.get_service()

        video_size = os.path.getsize(video_path)
        response = service.post(media_upload_url, data={
            "command": "INIT",
            "media_type": "video/mp4",
            "total_bytes": video_size,
            "media_category": "tweet_video",
        })
        if response.status_code != 202:
            logger_config.error(f"Twitter video INIT failed: {response.status_code} {response.json().get('error')}")
            return None

        media_id = response.json()['media_id_string']
        logger_config.success(f"Twitter video INIT OK, media ID: {media_id}")

        with open(video_path, 'rb') as video_file:
            segment_id = 0
            while True:
                chunk = video_file.read(4 * 1024 * 1024)
                if not chunk:
                    break
                response = service.post(media_upload_url, data={
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_id,
                }, files={"media": chunk})
                if response.status_code != 204:
                    logger_config.error(f"Twitter video APPEND failed: {response.status_code} {response.json().get('error')}")
                    return None
                segment_id += 1

        response = service.post(media_upload_url, data={"command": "FINALIZE", "media_id": media_id})
        if response.status_code != 201:
            logger_config.error(f"Twitter video FINALIZE failed: {response.status_code} {response.json().get('error')}")
            return None

        logger_config.success(f"Twitter video FINALIZE OK, media ID: {media_id}")
        return media_id

    def post(self, text, media_id=None, reply_id=None):
        if not text and not media_id:
            logger_config.error("Empty tweet payload.")
            return None

        payload = {"text": text} if text else {}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        if reply_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_id}

        response = self.get_service().post(TWEET_V2_URL, json=payload)
        if response.status_code != 201:
            logger_config.error(f"Tweet post failed: {response.status_code} {response.text}")
            return None

        logger_config.success("Tweet posted successfully.")
        return response.json()['data']['id']

    def publish(self, progress, final_video_path):
        tweet_text = progress.get("TWITTER_POST", "")
        if not tweet_text:
            logger_config.warning("No TWITTER_POST in progress file, skipping twitter publish.")
            return False

        tweet_id = self.post(tweet_text)
        if tweet_id:
            logger_config.success(f"Published to twitter with tweet ID: {tweet_id}")
            return True

        logger_config.error("Failed to publish to twitter.")
        return False
