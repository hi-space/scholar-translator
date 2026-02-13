import html
import logging
import os
import re
import unicodedata
from copy import copy
from string import Template
from typing import cast
import requests

from scholar_translator.cache import TranslationCache
from scholar_translator.config import ConfigManager

from tenacity import retry, retry_if_not_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential


logger = logging.getLogger(__name__)


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


class BaseTranslator:
    name = "base"
    envs = {}
    lang_map: dict[str, str] = {}
    CustomPrompt = False

    def __init__(self, lang_in: str, lang_out: str, model: str, ignore_cache: bool):
        lang_in = self.lang_map.get(lang_in.lower(), lang_in)
        lang_out = self.lang_map.get(lang_out.lower(), lang_out)
        self.lang_in = lang_in
        self.lang_out = lang_out
        self.model = model
        self.ignore_cache = ignore_cache

        self.cache = TranslationCache(
            self.name,
            {
                "lang_in": lang_in,
                "lang_out": lang_out,
                "model": model,
            },
        )

    def set_envs(self, envs):
        # Detach from self.__class__.envs
        # Cannot use self.envs = copy(self.__class__.envs)
        # because if set_envs called twice, the second call will override the first call
        self.envs = copy(self.envs)
        if ConfigManager.get_translator_by_name(self.name):
            self.envs = ConfigManager.get_translator_by_name(self.name)
        needUpdate = False
        for key in self.envs:
            if key in os.environ:
                self.envs[key] = os.environ[key]
                needUpdate = True
        if needUpdate:
            ConfigManager.set_translator_by_name(self.name, self.envs)
        if envs is not None:
            for key in envs:
                self.envs[key] = envs[key]
            ConfigManager.set_translator_by_name(self.name, self.envs)

    def add_cache_impact_parameters(self, k: str, v):
        """
        Add parameters that affect the translation quality to distinguish the translation effects under different parameters.
        :param k: key
        :param v: value
        """
        self.cache.add_params(k, v)

    def translate(self, text: str, ignore_cache: bool = False, **kwargs) -> str:
        """
        Translate the text, and the other part should call this method.
        :param text: text to translate
        :param ignore_cache: whether to ignore cache
        :param kwargs: additional parameters (e.g., rate_limit_params for babeldoc compatibility)
        :return: translated text
        """
        if not (self.ignore_cache or ignore_cache):
            cache = self.cache.get(text)
            if cache is not None:
                return cache

        translation = self.do_translate(text)
        self.cache.set(text, translation)
        return translation

    def do_translate(self, text: str) -> str:
        """
        Actual translate text, override this method
        :param text: text to translate
        :return: translated text
        """
        raise NotImplementedError

    def prompt(
        self, text: str, prompt_template: Template | None = None
    ) -> list[dict[str, str]]:
        try:
            return [
                {
                    "role": "user",
                    "content": cast(Template, prompt_template).safe_substitute(
                        {
                            "lang_in": self.lang_in,
                            "lang_out": self.lang_out,
                            "text": text,
                        }
                    ),
                }
            ]
        except AttributeError:  # `prompt_template` is None
            pass
        except Exception:
            logging.exception("Error parsing prompt, use the default prompt.")

        return [
            {
                "role": "user",
                "content": (
                    "You are a professional, authentic machine translation engine. "
                    "Only Output the translated text, do not include any other text."
                    "\n\n"
                    f"Translate the following markdown source text to {self.lang_out}. "
                    "Keep the formula notation {v*} unchanged. "
                    "Output translation directly without any additional text."
                    "\n\n"
                    f"Source Text: {text}"
                    "\n\n"
                    "Translated Text:"
                ),
            },
        ]

    def __str__(self):
        return f"{self.name} {self.lang_in} {self.lang_out} {self.model}"

    def get_rich_text_left_placeholder(self, id: int):
        return f"<b{id}>"

    def get_rich_text_right_placeholder(self, id: int):
        return f"</b{id}>"

    def get_formular_placeholder(self, id: int):
        return self.get_rich_text_left_placeholder(
            id
        ) + self.get_rich_text_right_placeholder(id)


class GoogleTranslator(BaseTranslator):
    name = "google"
    lang_map = {"ko": "ko"}

    def __init__(self, lang_in, lang_out, model, ignore_cache=False, **kwargs):
        super().__init__(lang_in, lang_out, model, ignore_cache)
        self.session = requests.Session()
        self.endpoint = "https://translate.google.com/m"
        self.headers = {
            "User-Agent": "Mozilla/4.0 (compatible;MSIE 6.0;Windows NT 5.1;SV1;.NET CLR 1.1.4322;.NET CLR 2.0.50727;.NET CLR 3.0.04506.30)"  # noqa: E501
        }

    def do_translate(self, text):
        text = text[:5000]  # google translate max length
        response = self.session.get(
            self.endpoint,
            params={"tl": self.lang_out, "sl": self.lang_in, "q": text},
            headers=self.headers,
        )
        re_result = re.findall(
            r'(?s)class="(?:t0|result-container)">(.*?)<', response.text
        )
        if response.status_code == 400:
            result = "IRREPARABLE TRANSLATION ERROR"
        else:
            response.raise_for_status()
            result = html.unescape(re_result[0])
        return remove_control_characters(result)


class BedrockTranslator(BaseTranslator):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html
    name = "bedrock"
    CustomPrompt = True

    # Model shortcuts mapping for convenience
    MODEL_MAP = {
        "claude-4.5-opus": "global.anthropic.claude-opus-4-5-20251101-v1:0",
        "claude-4.5-sonnet": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "claude-4.5-haiku": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    }

    envs = {
        "AWS_REGION": "us-west-2",
        "AWS_ACCESS_KEY_ID": None,
        "AWS_SECRET_ACCESS_KEY": None,
        "AWS_SESSION_TOKEN": None,
        "BEDROCK_MODEL_ID": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    }

    def __init__(
        self,
        lang_in,
        lang_out,
        model,
        envs=None,
        prompt=None,
        ignore_cache=False,
        **kwargs,
    ):
        # Check if boto3 is installed
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "boto3 is not installed. Install with: pip install scholar-translator[bedrock]"
            )

        self.set_envs(envs)

        # Resolve model shortcut to full Bedrock model ID
        if not model:
            model = self.envs["BEDROCK_MODEL_ID"]
        model = self.MODEL_MAP.get(model, model)

        super().__init__(lang_in, lang_out, model, ignore_cache)

        self.options = {
            "temperature": 0,
            "max_tokens": 2000,
        }
        self.prompttext = prompt

        # Initialize Bedrock client with authentication
        # Priority: IAM role (default) -> explicit credentials
        aws_region = self.envs.get("AWS_REGION") or "us-west-2"
        if not aws_region or aws_region.strip() == "":
            aws_region = "us-west-2"
        client_kwargs = {"region_name": aws_region}

        if self.envs["AWS_ACCESS_KEY_ID"] and self.envs["AWS_SECRET_ACCESS_KEY"]:
            client_kwargs["aws_access_key_id"] = self.envs["AWS_ACCESS_KEY_ID"]
            client_kwargs["aws_secret_access_key"] = self.envs["AWS_SECRET_ACCESS_KEY"]
            if self.envs["AWS_SESSION_TOKEN"]:
                client_kwargs["aws_session_token"] = self.envs["AWS_SESSION_TOKEN"]

        try:
            self.client = boto3.client("bedrock-runtime", **client_kwargs)
        except Exception as e:
            raise ValueError(
                f"Failed to initialize AWS Bedrock client: {e}\n"
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, "
                "or configure IAM role if running on AWS."
            )

        # Add cache impact parameters
        self.add_cache_impact_parameters("temperature", self.options["temperature"])
        self.add_cache_impact_parameters("max_tokens", self.options["max_tokens"])
        self.add_cache_impact_parameters("prompt", self.prompt("", self.prompttext))

        # Store ClientError for retry logic
        self.ClientError = ClientError

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        retry=retry_if_not_exception_type(ValueError),
        before_sleep=lambda retry_state: logger.warning(
            f"Bedrock rate limit or error, retrying in {retry_state.next_action.sleep} seconds... "
            f"(Attempt {retry_state.attempt_number}/5)"
        ),
    )
    def do_translate(self, text) -> str:
        import json
        from botocore.exceptions import ClientError

        # Construct Messages API format for Claude models
        messages = self.prompt(text, self.prompttext)

        # Convert to Bedrock format
        bedrock_messages = []
        for msg in messages:
            bedrock_messages.append({"role": msg["role"], "content": msg["content"]})

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.options["max_tokens"],
            "temperature": self.options["temperature"],
            "messages": bedrock_messages,
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model, body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            content = response_body["content"][0]["text"].strip()
            return content

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            # Don't retry on validation or access errors
            if error_code in ["ValidationException", "AccessDeniedException"]:
                raise ValueError(
                    f"AWS Bedrock error ({error_code}): {e.response['Error']['Message']}"
                )

            # Retry on throttling and service errors
            if error_code in [
                "ThrottlingException",
                "ServiceUnavailableException",
                "TooManyRequestsException",
            ]:
                raise  # Will be caught by retry decorator

            # Unknown error, log and raise
            logger.error(f"Unexpected Bedrock error: {error_code} - {e}")
            raise
