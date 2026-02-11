---
name: scholar-translator
description: Translate academic papers (PDF) while preserving formulas, charts, and layout using CLI commands. Use when users need to translate research papers, arXiv PDFs, or scientific documents with flexible options (page selection, output directories, language pairs). Trigger for '논문 번역', 'translate paper', 'translate PDF', or PDF translation tasks. Uses uvx to run scholar-translator CLI directly.
---

# Scholar Translator Skill

Translate academic PDF papers while preserving mathematical formulas, charts, tables, and layout using flexible CLI commands with full parameter control.

## When to Use This Skill

- User asks to translate academic papers, research PDFs, or arXiv papers
- User provides PDF file path or uploads a PDF
- User mentions "translate paper", "translate PDF", "논문 번역", or similar phrases
- User wants bilingual versions of scientific documents
- User needs to translate specific pages or sections (page range support)
- User wants to organize translations in custom directories

## Prerequisites

### UV/UVX Installation

This skill uses `uvx` to run scholar-translator directly from GitHub - no manual installation required.

If `uvx` is not available, install `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### AWS Credentials (Required for Bedrock)

To use AWS Bedrock translation service (recommended for quality), set these environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGION="us-west-2"
```

**Alternative:** Use Google Translate service (no credentials required, but lower quality for technical content).

## CLI Command Structure

### Basic Syntax

```bash
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator \
  <file> \
  [options]
```

### Quick Start Example

```bash
# Translate entire PDF to Korean using AWS Bedrock
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator \
  /path/to/paper.pdf

# Translate specific pages to Japanese
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator \
  /path/to/paper.pdf \
  --lang-out ja \
  --pages 1-10
```

## Core Parameters

| Parameter | Short | Description | Default | Required |
|-----------|-------|-------------|---------|----------|
| `file` | - | PDF file path (absolute or relative) | - | Yes |
| `--lang-in` | `-li` | Source language code | `auto` (detect) | No |
| `--lang-out` | `-lo` | Target language code | `ko` (Korean) | No |
| `--service` | `-s` | Translation service: `bedrock` or `google` | `bedrock` | No |
| `--model` | `-m` | Model ID (for Bedrock) | `claude-haiku-4.5` | No |

### Core Parameter Details

**`file` (required)**
- Absolute or relative path to PDF file
- Enclose in quotes if path contains spaces
- Example: `/home/user/papers/research.pdf` or `"./My Papers/paper.pdf"`

**`--lang-in` / `-li` (optional)**
- Source language code (e.g., `en`, `ja`, `zh`)
- Default: `auto` (automatic detection)
- Specify if auto-detection fails
- See Language Codes section for full list

**`--lang-out` / `-lo` (optional)**
- Target language code (e.g., `ko`, `en`, `ja`)
- Default: `ko` (Korean)
- Required if translating to non-Korean language

**`--service` / `-s` (optional)**
- `bedrock` - AWS Bedrock Claude models (high quality, requires AWS credentials)
- `google` - Google Translate (free, lower quality for technical content)
- Default: `bedrock`

**`--model` / `-m` (optional)**
- For Bedrock: `claude-haiku-4.5`, `claude-sonnet-4.5`, `claude-opus-4.5`
- For Google: ignored
- Default: `claude-haiku-4.5` (fast, cost-effective)

## Advanced Parameters

| Parameter | Short | Description | Default | Use Case |
|-----------|-------|-------------|---------|----------|
| `--pages` | `-p` | Page range to translate | All pages | Large docs, specific sections |
| `--output` | `-o` | Output directory path | Current dir | Organize translations |
| `--thread` | `-t` | Number of parallel threads | 4 | Speed up large docs |
| `--font-regex` | - | Font pattern for rendering | Auto | Fix font issues |
| `--ignore-cache` | - | Disable translation cache | False | Force re-translation |
| `--compatible` | `-cp` | Convert to PDF/A format | False | Compatibility |
| `--debug` | `-d` | Enable debug logging | False | Troubleshooting |

### Advanced Parameter Details

**`--pages` / `-p` (critical feature!)**
- Specify which pages to translate
- Syntax:
  - Single page: `-p 1`
  - Range: `-p 1-10`
  - Multiple ranges: `-p 1-3,7,10-15`
- Examples:
  - `-p 1` - Translate only abstract/introduction
  - `-p 1-5` - Translate first 5 pages
  - `-p 10-20` - Translate specific section
  - `-p 1,5,10` - Translate summary pages only

**`--output` / `-o` (important feature!)**
- Custom directory for output PDFs
- Creates directory if it doesn't exist
- Default: Same directory as input PDF
- Examples:
  - `-o /tmp/translations/` - Temporary location
  - `-o ./output/japanese/` - Organize by language
  - `-o ~/Documents/translated/` - User documents folder

**`--thread` / `-t`**
- Number of parallel translation threads
- Default: 4 (good balance)
- Increase for large documents: `-t 8` or `-t 12`
- Reduce if hitting API rate limits: `-t 2`

**`--font-regex`**
- Pattern to match fonts for language-specific rendering
- Example: `--font-regex "NanumGothic.*"` for Korean
- Use when output PDF has missing characters or rendering issues

**`--ignore-cache`**
- Skip cached translations and force re-translation
- Useful when previous results were incorrect
- Adds processing time but ensures fresh results

## Language Codes

Supported language codes for translation:

| Code | Language | Direction | Notes |
|------|----------|-----------|-------|
| `auto` | Auto-detect | Source only | Default for --lang-in |
| `ko` | Korean | Both | Default target language |
| `en` | English | Both | Common source language |
| `ja` | Japanese | Both | Full support |
| `zh` | Chinese | Both | Simplified Chinese |
| `fr` | French | Both | Full support |
| `de` | German | Both | Full support |
| `es` | Spanish | Both | Full support |
| `pt` | Portuguese | Both | Full support |
| `ru` | Russian | Both | Cyrillic support |
| `it` | Italian | Both | Full support |
| `ar` | Arabic | Both | RTL layout preserved |
| `hi` | Hindi | Both | Devanagari support |

**Usage:**
- Source language (`--lang-in`): Defaults to auto-detection, specify if needed
- Target language (`--lang-out`): Required if not using default `ko`

## Translation Services

### AWS Bedrock (Recommended)

**Quality:** High - Uses Claude 4.5 models specialized for translation

**Requirements:**
- AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
- AWS region with Claude model access (us-west-2, us-east-1)

**Available Models:**

| Model | Speed | Quality | Cost per page | When to Use |
|-------|-------|---------|---------------|-------------|
| `claude-haiku-4.5` | Fast | Good | ~$0.02-0.05 | Standard papers, previews, batch jobs (default) |
| `claude-sonnet-4.5` | Medium | High | ~$0.15-0.30 | Technical papers, complex terminology, critical translations |

**When to use Haiku (default):**
- Standard academic papers without complex terminology
- Quick previews or rough translations
- Large documents where cost is a concern
- Batch translation of multiple papers
- Most general-purpose translation tasks

**When to use Sonnet:**
- Technical papers with domain-specific terminology
- Papers requiring nuanced translation (legal, medical, etc.)
- Critical translations for publication or submission
- When translation quality is more important than speed/cost

### Google Translate

**Quality:** Good for general content, lower for technical/academic

**Requirements:** None (free service)

**When to use Google Translate:**
- No AWS credentials available
- Quick preview or exploratory translation
- Non-technical or general content
- Good for - Quick previews, non-technical content, when AWS unavailable

## Output Files

Every translation creates **two PDF files**:

### 1. Mono Version (`{filename}-{lang}-mono.pdf`)
- Contains only translated text
- Original text is replaced with translation
- Smaller file size
- **Best for:** Reading exclusively in target language

### 2. Dual Version (`{filename}-{lang}-dual.pdf`)
- Contains both original and translated text
- Translation appears alongside or below original
- Larger file size
- **Best for:** Academic review, comparison, learning, verification

**File Location:**
- Default: Same directory as input PDF
- With `--output`: Custom directory specified

**Example:**
```bash
# Input: /home/user/papers/research.pdf
# Output (default):
#   /home/user/papers/research-ko-mono.pdf
#   /home/user/papers/research-ko-dual.pdf
#
# Output (with -o /tmp/translations/):
#   /tmp/translations/research-ko-mono.pdf
#   /tmp/translations/research-ko-dual.pdf
```

## Workflow Pattern

**Standard Translation Steps:**
1. Check AWS credentials: `echo $AWS_ACCESS_KEY_ID`
2. Verify file exists: `ls -lh /path/to/paper.pdf`
3. Execute command with appropriate parameters
4. Verify output files created: `ls -lh output-dir/`
5. If errors occur: Check credentials, file paths, or use Google Translate fallback

## Error Handling

**AWS AccessDeniedException:** Use `--service google` or set AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)

**File Not Found:** Verify file exists (`ls -lh file.pdf`), use absolute path (`realpath`), quote paths with spaces

**Permission Denied:** Check write permissions or use `--output` to specify different directory

## Best Practices

**Paths:** Use absolute paths, quote spaces: `"/path with/spaces.pdf"`

**Performance:** Default 4 threads; increase for large docs (`-t 8`), reduce for rate limits (`-t 2`)

**Organization:** Use `--output` for language/project-specific directories

**Page Selection:** Use `--pages` for large PDFs to save time/cost (e.g., `-p 1-10` for intro/conclusion)

## Command Cheat Sheet

```bash
# Basic translation (Korean, Bedrock Haiku)
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator paper.pdf

# Specify target language
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator paper.pdf --lang-out ja

# Translate specific pages only
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator paper.pdf --pages 1-10

# Custom output directory
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator paper.pdf --output /tmp/translations/

# High-quality translation (Sonnet)
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator paper.pdf \
  --service bedrock --model claude-sonnet-4.5

# Google Translate (no AWS credentials)
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator paper.pdf --service google

# Fast translation (more threads)
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator paper.pdf --thread 12

# Complete example with all options
uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator \
  /path/to/paper.pdf \
  --lang-in en \
  --lang-out ja \
  --service bedrock \
  --model claude-sonnet-4.5 \
  --pages 1-20 \
  --output ~/translations/japanese/ \
  --thread 8

# Batch translation to multiple languages
for lang in ja fr de es; do
  uvx --from git+https://github.com/hi-space/scholar-translator.git scholar-translator \
    paper.pdf \
    --lang-out $lang \
    --output ./translations/$lang/
done
```
