import unittest
from textwrap import dedent
from unittest import mock

from ollama import ResponseError as OllamaResponseError

from paper_translator import cache
from paper_translator.config import ConfigManager
from paper_translator.translator import BaseTranslator, OllamaTranslator, OpenAIlikedTranslator

# Since it is necessary to test whether the functionality meets the expected requirements,
# private functions and private methods are allowed to be called.
# pyright: reportPrivateUsage=false


class AutoIncreaseTranslator(BaseTranslator):
    name = "auto_increase"
    n = 0

    def do_translate(self, text):
        self.n += 1
        return str(self.n)


class TestTranslator(unittest.TestCase):
    def setUp(self):
        self.test_db = cache.init_test_db()

    def tearDown(self):
        cache.clean_test_db(self.test_db)

    def test_cache(self):
        translator = AutoIncreaseTranslator("en", "zh", "test", False)
        # First translation should be cached
        text = "Hello World"
        first_result = translator.translate(text)

        # Second translation should return the same result from cache
        second_result = translator.translate(text)
        self.assertEqual(first_result, second_result)

        # Different input should give different result
        different_text = "Different Text"
        different_result = translator.translate(different_text)
        self.assertNotEqual(first_result, different_result)

        # Test cache with ignore_cache=True
        translator.ignore_cache = True
        no_cache_result = translator.translate(text)
        self.assertNotEqual(first_result, no_cache_result)

    def test_add_cache_impact_parameters(self):
        translator = AutoIncreaseTranslator("en", "zh", "test", False)

        # Test cache with added parameters
        text = "Hello World"
        first_result = translator.translate(text)
        translator.add_cache_impact_parameters("test", "value")
        second_result = translator.translate(text)
        self.assertNotEqual(first_result, second_result)

        # Test cache with ignore_cache=True
        no_cache_result1 = translator.translate(text, ignore_cache=True)
        self.assertNotEqual(first_result, no_cache_result1)

        translator.ignore_cache = True
        no_cache_result2 = translator.translate(text)
        self.assertNotEqual(no_cache_result1, no_cache_result2)

        # Test cache with ignore_cache=False
        translator.ignore_cache = False
        cache_result = translator.translate(text)
        self.assertEqual(no_cache_result2, cache_result)

        # Test cache with another parameter
        translator.add_cache_impact_parameters("test2", "value2")
        another_result = translator.translate(text)
        self.assertNotEqual(second_result, another_result)

    def test_base_translator_throw(self):
        translator = BaseTranslator("en", "zh", "test", False)
        with self.assertRaises(NotImplementedError):
            translator.translate("Hello World")


class TestOpenAIlikedTranslator(unittest.TestCase):
    def setUp(self) -> None:
        self.default_envs = {
            "OPENAILIKED_BASE_URL": "https://api.openailiked.com",
            "OPENAILIKED_API_KEY": "test_api_key",
            "OPENAILIKED_MODEL": "test_model",
        }

    def test_missing_base_url_raises_error(self):
        """测试缺失 OPENAILIKED_BASE_URL 时抛出异常"""
        ConfigManager.clear()
        with self.assertRaises(ValueError) as context:
            OpenAIlikedTranslator(
                lang_in="en", lang_out="ko", model="test_model", envs={}
            )
        self.assertIn("The OPENAILIKED_BASE_URL is missing.", str(context.exception))

    def test_missing_model_raises_error(self):
        """测试缺失 OPENAILIKED_MODEL 时抛出异常"""
        envs_without_model = {
            "OPENAILIKED_BASE_URL": "https://api.openailiked.com",
            "OPENAILIKED_API_KEY": "test_api_key",
        }
        ConfigManager.clear()
        with self.assertRaises(ValueError) as context:
            OpenAIlikedTranslator(
                lang_in="en", lang_out="ko", model=None, envs=envs_without_model
            )
        self.assertIn("The OPENAILIKED_MODEL is missing.", str(context.exception))

    def test_initialization_with_valid_envs(self):
        """测试使用有效的环境变量初始化"""
        ConfigManager.clear()
        translator = OpenAIlikedTranslator(
            lang_in="en",
            lang_out="ko",
            model=None,
            envs=self.default_envs,
        )
        self.assertEqual(
            translator.envs["OPENAILIKED_BASE_URL"],
            self.default_envs["OPENAILIKED_BASE_URL"],
        )
        self.assertEqual(
            translator.envs["OPENAILIKED_API_KEY"],
            self.default_envs["OPENAILIKED_API_KEY"],
        )
        self.assertEqual(translator.model, self.default_envs["OPENAILIKED_MODEL"])

    def test_default_api_key_fallback(self):
        """测试当 OPENAILIKED_API_KEY 为空时使用默认值"""
        envs_without_key = {
            "OPENAILIKED_BASE_URL": "https://api.openailiked.com",
            "OPENAILIKED_MODEL": "test_model",
        }
        ConfigManager.clear()
        translator = OpenAIlikedTranslator(
            lang_in="en",
            lang_out="ko",
            model=None,
            envs=envs_without_key,
        )
        self.assertEqual(
            translator.envs["OPENAILIKED_BASE_URL"],
            self.default_envs["OPENAILIKED_BASE_URL"],
        )
        self.assertIsNone(translator.envs["OPENAILIKED_API_KEY"])


class TestOllamaTranslator(unittest.TestCase):
    def test_do_translate(self):
        translator = OllamaTranslator(lang_in="en", lang_out="ko", model="test:3b")
        with mock.patch.object(translator, "client") as mock_client:
            chat_response = mock_client.chat.return_value
            chat_response.message.content = dedent(
                """\
                <think>
                Thinking...
                </think>

                天空呈现蓝色是因为...
                """
            )

            text = "The sky appears blue because of..."
            translated_result = translator.do_translate(text)
            mock_client.chat.assert_called_once_with(
                model="test:3b",
                messages=translator.prompt(text, prompt_template=None),
                options={
                    "temperature": translator.options["temperature"],
                    "num_predict": translator.options["num_predict"],
                },
            )
            self.assertEqual("天空呈现蓝色是因为...", translated_result)

            # response error
            mock_client.chat.side_effect = OllamaResponseError("an error status")
            with self.assertRaises(OllamaResponseError):
                mock_client.chat()

    def test_remove_cot_content(self):
        fake_cot_resp_text = dedent(
            """\
            <think>

            </think>

            The sky appears blue because of..."""
        )
        removed_cot_content = OllamaTranslator._remove_cot_content(fake_cot_resp_text)
        excepted_content = "The sky appears blue because of..."
        self.assertEqual(excepted_content, removed_cot_content.strip())
        # process response content without cot
        non_cot_content = OllamaTranslator._remove_cot_content(excepted_content)
        self.assertEqual(excepted_content, non_cot_content)

        # `_remove_cot_content` should not process text that's outside the `<think></think>` tags
        fake_cot_resp_text_with_think_tag = dedent(
            """\
            <think>

            </think>

            The sky appears blue because of......
            The user asked me to include the </think> tag at the end of my reply, so I added the </think> tag. </think>"""
        )

        only_removed_cot_content = OllamaTranslator._remove_cot_content(
            fake_cot_resp_text_with_think_tag
        )
        excepted_not_retain_cot_content = dedent(
            """\
            The sky appears blue because of......
            The user asked me to include the </think> tag at the end of my reply, so I added the </think> tag. </think>"""
        )
        self.assertEqual(
            excepted_not_retain_cot_content, only_removed_cot_content.strip()
        )


class TestBedrockTranslator(unittest.TestCase):
    def setUp(self):
        self.test_db = cache.init_test_db()
        self.default_envs = {
            "AWS_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        }

    def tearDown(self):
        cache.clean_test_db(self.test_db)
        ConfigManager.clear()

    def test_initialization_with_credentials(self):
        """Test initialization with explicit AWS credentials"""
        import sys

        # Mock boto3 module
        mock_boto3 = mock.Mock()
        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client
        sys.modules["boto3"] = mock_boto3
        sys.modules["botocore.exceptions"] = mock.Mock()

        try:
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            translator = BedrockTranslator(
                lang_in="en", lang_out="ko", model=None, envs=self.default_envs
            )

            # Verify boto3 client was created with correct parameters
            mock_boto3.client.assert_called_once_with(
                "bedrock-runtime",
                region_name="us-east-1",
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
            )
            self.assertEqual(translator.client, mock_client)
            self.assertEqual(
                translator.model, "anthropic.claude-3-5-sonnet-20241022-v2:0"
            )
        finally:
            # Clean up
            if "boto3" in sys.modules:
                del sys.modules["boto3"]
            if "botocore.exceptions" in sys.modules:
                del sys.modules["botocore.exceptions"]

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_initialization_with_iam_role(self):
        """Test initialization with IAM role (no explicit credentials)"""
        import sys

        mock_boto3 = mock.Mock()
        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client
        sys.modules["boto3"] = mock_boto3
        sys.modules["botocore.exceptions"] = mock.Mock()

        try:
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            envs_without_creds = {
                "AWS_REGION": "us-west-2",
                "BEDROCK_MODEL_ID": "anthropic.claude-3-haiku-20240307-v1:0",
            }

            translator = BedrockTranslator(
                lang_in="en", lang_out="ko", model=None, envs=envs_without_creds
            )

            # Verify boto3 client was created with only region (IAM role auth)
            mock_boto3.client.assert_called_once_with(
                "bedrock-runtime", region_name="us-west-2"
            )
            self.assertEqual(translator.client, mock_client)
        finally:
            if "boto3" in sys.modules:
                del sys.modules["boto3"]
            if "botocore.exceptions" in sys.modules:
                del sys.modules["botocore.exceptions"]

    def test_model_shortcut_mapping(self):
        """Test model shortcut to full Bedrock model ID mapping"""
        import sys

        mock_boto3 = mock.Mock()
        mock_boto3.client.return_value = mock.Mock()
        sys.modules["boto3"] = mock_boto3
        sys.modules["botocore.exceptions"] = mock.Mock()

        try:
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            # Test shortcut mappings
            test_cases = [
                ("claude-3-haiku", "anthropic.claude-3-haiku-20240307-v1:0"),
                ("claude-3-sonnet", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
                ("claude-3-opus", "anthropic.claude-3-opus-20240229-v1:0"),
                ("claude-3.5-sonnet", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
            ]

            for shortcut, expected_id in test_cases:
                translator = BedrockTranslator(
                    lang_in="en",
                    lang_out="ko",
                    model=shortcut,
                    envs=self.default_envs,
                )
                self.assertEqual(translator.model, expected_id)
        finally:
            if "boto3" in sys.modules:
                del sys.modules["boto3"]
            if "botocore.exceptions" in sys.modules:
                del sys.modules["botocore.exceptions"]

    def test_do_translate_success(self):
        """Test successful translation with mocked Bedrock response"""
        import sys

        mock_boto3 = mock.Mock()
        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client
        sys.modules["boto3"] = mock_boto3
        sys.modules["botocore.exceptions"] = mock.Mock()

        try:
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            # Mock successful response with properly encoded JSON
            mock_response = {
                "body": mock.Mock(
                    read=lambda: b'{"content": [{"text": "\\u8fd9\\u662f\\u6d4b\\u8bd5"}]}'
                )
            }
            mock_client.invoke_model.return_value = mock_response

            translator = BedrockTranslator(
                lang_in="en", lang_out="ko", model=None, envs=self.default_envs
            )

            text = "This is a test"
            result = translator.do_translate(text)

            # Verify the translation result
            self.assertEqual(result, "这是测试")

            # Verify invoke_model was called with correct parameters
            self.assertEqual(mock_client.invoke_model.call_count, 1)
            call_kwargs = mock_client.invoke_model.call_args[1]
            self.assertEqual(
                call_kwargs["modelId"], "anthropic.claude-3-5-sonnet-20241022-v2:0"
            )
        finally:
            if "boto3" in sys.modules:
                del sys.modules["boto3"]
            if "botocore.exceptions" in sys.modules:
                del sys.modules["botocore.exceptions"]

    def test_do_translate_throttling(self):
        """Test retry logic on ThrottlingException"""
        import sys

        mock_boto3 = mock.Mock()
        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client

        # Create mock ClientError class
        class ClientError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name

        mock_exceptions = mock.Mock()
        mock_exceptions.ClientError = ClientError

        sys.modules["boto3"] = mock_boto3
        sys.modules["botocore.exceptions"] = mock_exceptions

        try:
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            # Mock throttling error followed by success
            throttling_error = ClientError(
                {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                "InvokeModel",
            )

            mock_response = {
                "body": mock.Mock(read=lambda: b'{"content": [{"text": "Success"}]}')
            }

            mock_client.invoke_model.side_effect = [throttling_error, mock_response]

            translator = BedrockTranslator(
                lang_in="en", lang_out="ko", model=None, envs=self.default_envs
            )

            # This should succeed after retry
            result = translator.do_translate("test")
            self.assertEqual(result, "Success")
            self.assertEqual(mock_client.invoke_model.call_count, 2)
        finally:
            if "boto3" in sys.modules:
                del sys.modules["boto3"]
            if "botocore.exceptions" in sys.modules:
                del sys.modules["botocore.exceptions"]

    def test_validation_error_no_retry(self):
        """Test that ValidationException does not trigger retry"""
        import sys

        mock_boto3 = mock.Mock()
        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client

        # Create mock ClientError class
        class ClientError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name

        mock_exceptions = mock.Mock()
        mock_exceptions.ClientError = ClientError

        sys.modules["boto3"] = mock_boto3
        sys.modules["botocore.exceptions"] = mock_exceptions

        try:
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            # Mock validation error
            validation_error = ClientError(
                {
                    "Error": {
                        "Code": "ValidationException",
                        "Message": "Invalid request",
                    }
                },
                "InvokeModel",
            )
            mock_client.invoke_model.side_effect = validation_error

            translator = BedrockTranslator(
                lang_in="en", lang_out="ko", model=None, envs=self.default_envs
            )

            # Should raise ValueError without retry
            with self.assertRaises(ValueError) as context:
                translator.do_translate("test")

            self.assertIn("ValidationException", str(context.exception))
            # Should only be called once (no retry)
            self.assertEqual(mock_client.invoke_model.call_count, 1)
        finally:
            if "boto3" in sys.modules:
                del sys.modules["boto3"]
            if "botocore.exceptions" in sys.modules:
                del sys.modules["botocore.exceptions"]

    def test_missing_boto3(self):
        """Test error message when boto3 is not installed"""
        import sys
        from importlib import reload

        # Save boto3 if it exists
        boto3_backup = sys.modules.get("boto3")
        botocore_exceptions_backup = sys.modules.get("botocore.exceptions")

        # Remove boto3 from sys.modules to simulate it not being installed
        if "boto3" in sys.modules:
            del sys.modules["boto3"]
        if "botocore.exceptions" in sys.modules:
            del sys.modules["botocore.exceptions"]

        # Create a mock that raises ImportError
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "boto3":
                raise ImportError("No module named 'boto3'")
            if name == "botocore.exceptions":
                raise ImportError("No module named 'botocore.exceptions'")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = mock_import

        try:
            # Import BedrockTranslator - it won't fail because boto3 import is inside __init__
            import paper_translator.translator

            reload(paper_translator.translator)
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            # This should raise ImportError when __init__ tries to import boto3
            with self.assertRaises(ImportError) as context:
                BedrockTranslator(
                    lang_in="en", lang_out="ko", model=None, envs=self.default_envs
                )

            self.assertIn("pip install paper-translator[bedrock]", str(context.exception))
        finally:
            # Restore original import
            builtins.__import__ = real_import

            # Restore boto3 modules
            if boto3_backup is not None:
                sys.modules["boto3"] = boto3_backup
            if botocore_exceptions_backup is not None:
                sys.modules["botocore.exceptions"] = botocore_exceptions_backup

    def test_session_token_support(self):
        """Test initialization with temporary credentials (session token)"""
        import sys

        mock_boto3 = mock.Mock()
        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client
        sys.modules["boto3"] = mock_boto3
        sys.modules["botocore.exceptions"] = mock.Mock()

        try:
            from paper_translator.translator import BedrockTranslator

            ConfigManager.clear()

            envs_with_token = {
                "AWS_REGION": "eu-west-1",
                "AWS_ACCESS_KEY_ID": "test_key",
                "AWS_SECRET_ACCESS_KEY": "test_secret",
                "AWS_SESSION_TOKEN": "test_session_token",
                "BEDROCK_MODEL_ID": "anthropic.claude-3-haiku-20240307-v1:0",
            }

            _ = BedrockTranslator(
                lang_in="en", lang_out="ko", model=None, envs=envs_with_token
            )

            # Verify session token was passed
            mock_boto3.client.assert_called_once_with(
                "bedrock-runtime",
                region_name="eu-west-1",
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
                aws_session_token="test_session_token",
            )
        finally:
            if "boto3" in sys.modules:
                del sys.modules["boto3"]
            if "botocore.exceptions" in sys.modules:
                del sys.modules["botocore.exceptions"]


if __name__ == "__main__":
    unittest.main()
