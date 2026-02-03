from mcp.server import Server
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from paper_translator import translate_stream
from paper_translator.config import ConfigManager
from pathlib import Path
import json

import contextlib
import io
import os


def create_mcp_app() -> FastMCP:
    mcp = FastMCP("paper-translator")

    @mcp.tool()
    async def translate_pdf(
        file: str,
        lang_in: str,
        lang_out: str,
        service: str = "bedrock",
        model: str = "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        thread: int = 4,
        ctx: Context = None,
    ) -> str:
        """
        Translate a PDF file using various translation services.

        Args:
            file: Absolute path to the input PDF file
            lang_in: Source language code (e.g., 'en', 'ko', 'zh'). Use 'auto' for automatic detection
            lang_out: Target language code (e.g., 'en', 'ko', 'zh')
            service: Translation service to use. Options:
                - 'bedrock': AWS Bedrock (Claude models, requires AWS credentials)
                - 'google': Google Translate (default, free)
                - 'openai': OpenAI API (requires OPENAI_API_KEY)
                - 'deepl': DeepL API (requires DEEPL_AUTH_KEY)
                - 'ollama': Local Ollama (requires OLLAMA_HOST)
                - 'azure': Azure OpenAI (requires AZURE_ENDPOINT and AZURE_API_KEY)
            model: Model identifier for the translation service:
                - For bedrock: Full model ID or shortcuts like 'claude-4.5-sonnet', 'claude-haiku-4.5', 'sonnet', 'haiku'
                  Default: 'global.anthropic.claude-sonnet-4-5-20250929-v1:0'
                - For openai: 'gpt-4', 'gpt-3.5-turbo', etc.
                - For ollama: 'llama2', 'mistral', etc.
            thread: Number of parallel translation threads (default: 4)

        Environment variables required by service:
            - bedrock: AWS_REGION, AWS_ACCESS_KEY_ID (optional if using IAM role), AWS_SECRET_ACCESS_KEY (optional)
            - openai: OPENAI_API_KEY, OPENAI_BASE_URL (optional)
            - deepl: DEEPL_AUTH_KEY
            - ollama: OLLAMA_HOST, OLLAMA_MODEL
            - azure: AZURE_ENDPOINT, AZURE_API_KEY

        Returns:
            Success message with paths to the generated mono and dual PDF files
        """

        with open(file, "rb") as f:
            file_bytes = f.read()

        await ctx.log(
            level="info",
            message=f"Starting translation of {file} using {service} with model {model}",
        )

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                doc_mono_bytes, doc_dual_bytes = translate_stream(
                    file_bytes,
                    lang_in=lang_in,
                    lang_out=lang_out,
                    service=service,
                    model=model,
                    thread=thread,
                )

            await ctx.log(level="info", message="Translation complete")

            output_path = Path(os.path.dirname(file))
            filename = os.path.splitext(os.path.basename(file))[0]
            doc_mono = output_path / f"{filename}-{lang_out}-mono.pdf"
            doc_dual = output_path / f"{filename}-{lang_out}-dual.pdf"

            with open(doc_mono, "wb") as f:
                f.write(doc_mono_bytes)
            with open(doc_dual, "wb") as f:
                f.write(doc_dual_bytes)

            return f"""Translation complete!

Service: {service}
Model: {model}
Languages: {lang_in} → {lang_out}

Output files:
- Mono (translated only): {doc_mono.absolute()}
- Dual (original + translated): {doc_dual.absolute()}
"""
        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            return f"Error: {error_msg}"

    @mcp.tool()
    async def analyze_pdf(
        file: str,
        ctx: Context = None,
    ) -> str:
        """
        Analyze PDF structure without translating.

        Args:
            file: Absolute path to the input PDF file

        Returns:
            JSON string with PDF analysis: page count, detected languages, text regions, formulas, layout info
        """
        try:
            from paper_translator.converter import TranslateConverter
            from paper_translator.doclayout import OnnxModel
            from pdfminer.pdfpage import PDFPage
            from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
            from pdfminer.converter import PDFPageAggregator
            from pdfminer.layout import LAParams, LTTextBox, LTChar

            await ctx.log(level="info", message=f"Analyzing PDF: {file}")

            with open(file, "rb") as f:
                # Count pages
                pages = list(PDFPage.get_pages(f))
                page_count = len(pages)

                # Basic text extraction
                f.seek(0)
                rsrcmgr = PDFResourceManager()
                laparams = LAParams()
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)

                text_regions = 0
                total_chars = 0
                fonts_used = set()

                for page in PDFPage.get_pages(f):
                    interpreter.process_page(page)
                    layout = device.get_result()
                    for element in layout:
                        if isinstance(element, LTTextBox):
                            text_regions += 1
                            total_chars += len(element.get_text())
                            for item in element:
                                if hasattr(item, '__iter__'):
                                    for char in item:
                                        if isinstance(char, LTChar):
                                            fonts_used.add(char.fontname)

            analysis = {
                "file": file,
                "page_count": page_count,
                "text_regions": text_regions,
                "total_characters": total_chars,
                "fonts_detected": list(fonts_used),
                "status": "Analysis complete"
            }

            await ctx.log(level="info", message="PDF analysis complete")
            return json.dumps(analysis, indent=2)

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            return json.dumps({"error": error_msg})

    @mcp.tool()
    async def configure_service(
        service: str,
        config: dict,
        ctx: Context = None,
    ) -> str:
        """
        Update translator service configuration via ConfigManager.

        Args:
            service: Service name (e.g., 'bedrock', 'google', 'openai')
            config: Configuration dictionary (e.g., {"AWS_REGION": "us-west-2", "BEDROCK_MODEL_ID": "..."})

        Returns:
            Success message or error
        """
        try:
            await ctx.log(level="info", message=f"Updating configuration for {service}")

            config_manager = ConfigManager.get_instance()

            # Validate service name
            valid_services = ["bedrock", "google", "openai", "deepl", "ollama", "azure"]
            if service not in valid_services:
                return f"Error: Invalid service '{service}'. Valid services: {', '.join(valid_services)}"

            # Update configuration
            for key, value in config.items():
                config_manager.set(service, key, value)

            await ctx.log(level="info", message=f"Configuration updated for {service}")
            return f"Successfully updated configuration for {service}: {json.dumps(config, indent=2)}"

        except Exception as e:
            error_msg = f"Configuration update failed: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            return f"Error: {error_msg}"

    @mcp.resource("config://services")
    async def list_services() -> str:
        """List available translation services and their requirements"""
        services = {
            "bedrock": {
                "name": "AWS Bedrock",
                "description": "AWS Bedrock with Claude models (Sonnet 4.5, Haiku 4.5)",
                "default_model": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                "required_env": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                "optional_env": ["AWS_SESSION_TOKEN", "BEDROCK_MODEL_ID"]
            },
            "google": {
                "name": "Google Translate",
                "description": "Google Translate (free, no API key required)",
                "default_model": None,
                "required_env": [],
                "optional_env": []
            }
        }
        return json.dumps(services, indent=2)

    @mcp.resource("config://models/{service}")
    async def list_models(service: str) -> str:
        """List available models for a service"""
        models = {
            "bedrock": {
                "claude-4.5-sonnet": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                "claude-haiku-4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
                "claude-3.5-sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
                "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
                "sonnet": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                "haiku": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
            },
            "google": {
                "default": "Google Translate does not use explicit models"
            }
        }

        if service not in models:
            return json.dumps({"error": f"Unknown service: {service}"})

        return json.dumps(models[service], indent=2)

    @mcp.resource("config://languages")
    async def list_languages() -> str:
        """List supported language codes"""
        languages = {
            "ko": "Korean",
            "en": "English",
            "ja": "Japanese",
            "zh": "Simplified Chinese",
            "zh-CN": "Simplified Chinese",
            "zh-TW": "Traditional Chinese",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "it": "Italian",
            "ru": "Russian",
            "ar": "Arabic",
            "auto": "Auto-detect (for source language)"
        }
        return json.dumps(languages, indent=2)

    return mcp


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(request.scope, request.receive, request._send) as (
            read_stream,
            write_stream,
        ):
            await mcp_server.run(
                read_stream, write_stream, mcp_server.create_initialization_options()
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    import argparse

    mcp = create_mcp_app()
    mcp_server = mcp._mcp_server
    parser = argparse.ArgumentParser(description="Run MCP SSE-based PDF2ZH server")

    parser.add_argument(
        "--sse",
        default=False,
        action="store_true",
        help="Run the server with SSE transport or STDIO",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", required=False, help="Host to bind"
    )
    parser.add_argument(
        "--port", type=int, default=3001, required=False, help="Port to bind"
    )

    args = parser.parse_args()
    if args.sse and args.host and args.port:
        import uvicorn

        starlette_app = create_starlette_app(mcp_server, debug=True)
        uvicorn.run(starlette_app, host=args.host, port=args.port)
    else:
        mcp.run()
