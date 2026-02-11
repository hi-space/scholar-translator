<div align="center">

<h2 id="title">Scholar Translator</h2>

[English](README.md) | **한국어**

</div>

<h2 id="updates">1. 이것은 무엇을 하나요?</h2>

**한국어 번역에 최적화된** AWS Bedrock 기반 논문 PDF 번역 도구입니다.

- 📊 수식, 차트, 목차, 주석 보존
- 🇰🇷 **한국어 번역에 최적화** - 적절한 타이포그래피 및 폰트 사용
- 🤖 **AWS Bedrock 통합** - Claude Haiku 4.5가 기본 모델
- 🌐 [다양한 언어](#usage) 및 번역 서비스 지원
- 🛠️ [CLI 도구](#usage), [GUI](#install), [Python API](#api), [MCP Server](#mcp-server) 제공
- 🐳 간편한 배포를 위한 [Docker 지원](#docker)

<div align="center">
<img src="./docs/images/preview.gif" width="80%"/>
</div>

**빠른 시작:**

```bash
# uv 설치 (아직 설치하지 않은 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 클론 및 설치
git clone https://github.com/hi-space/paper-pdf-translator.git
cd paper-pdf-translator
uv sync

# AWS 인증 정보 설정
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# 논문 번역
uv run scholar-translator your-paper.pdf
```

<h2 id="use-section">2. 설치 및 사용법</h2>

### 3.1 사전 요구사항

- **Python**: 3.10 - 3.12 (3.13은 아직 완전히 지원되지 않음)
- **AWS 계정**: 기본 Bedrock 서비스에 필요
  - AWS Access Key ID 및 Secret Access Key
  - 리전에서 Bedrock API 액세스 활성화 필요
  - 또는 대안으로 Google Translate 사용 (API 키 불필요)

<h3 id="install">3.2 설치</h3>

<details open>
  <summary>3.2.1 uv로 설치 (권장 - 빠르고 안정적)</summary>

1. **uv 설치 (아직 설치하지 않은 경우):**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **클론 및 설정:**

   ```bash
   git clone https://github.com/hi-space/paper-pdf-translator.git
   cd paper-pdf-translator
   uv sync
   ```

3. **AWS 인증 정보 설정:**

   ```bash
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export AWS_REGION="us-west-2"
   ```

   또는 `~/.aws/credentials` 파일로 설정할 수 있습니다.

4. **PDF 번역:**

   ```bash
   # 기본값: 영어 → 한국어, AWS Bedrock Claude Haiku 4.5 사용
   uv run scholar-translator document.pdf

   # 언어 지정
   uv run scholar-translator document.pdf -li en -lo ko

   # Google Translate 사용 (AWS 불필요)
   uv run scholar-translator document.pdf -s google
   ```

</details>

<details open>
  <summary>3.2.2 그래픽 사용자 인터페이스 (GUI)</summary>

1. **GUI 설치 및 실행:**

   ```bash
   # uv로 설치한 후 (3.2.1 참조)
   uv run scholar-translator -i

   # 또는 pip 설치 후
   scholar-translator -i
   ```

2. **브라우저에서 열기:**

   ```
   http://localhost:7860/
   ```

3. **기능:**
   - 웹 인터페이스를 통한 PDF 파일 업로드
   - 소스 및 대상 언어 선택
   - 번역 서비스 선택 (Bedrock 또는 Google)
   - 번역된 PDF 다운로드 (단일 및 이중 버전)

   <img src="./docs/images/gui.gif" width="500"/>

</details>

<details open>
  <summary>3.2.3 Docker 배포</summary>

1. **빌드 및 실행:**

   ```bash
   docker compose up
   ```

   또는 수동으로:

   ```bash
   docker build -t scholar-translator .
   docker run -d -p 7860:7860 \
     -e AWS_ACCESS_KEY_ID="your-key" \
     -e AWS_SECRET_ACCESS_KEY="your-secret" \
     -e AWS_REGION="us-west-2" \
     scholar-translator
   ```

2. **GUI 액세스:**

   ```
   http://localhost:7860/
   ```

클라우드 배포의 경우:

Kubernetes와 같은 표준 Docker 배포 방법 또는 컨테이너 오케스트레이션 플랫폼을 사용하세요.
</details>

<details open>
  <summary>3.2.4 MCP Server (Model Context Protocol)</summary>

**Scholar Translator**는 Claude Desktop 및 Claude Code와 같은 AI 어시스턴트와의 통합을 위한 MCP 서버를 포함합니다.

### 사전 요구사항

MCP 서버를 사용하기 전에 패키지를 설치해야 합니다:

**옵션 A: 전역 설치 (최종 사용자용 권장)**
```bash
# pip로 설치
pip install scholar-translator

# 또는 uv로 설치
uv tool install scholar-translator

# 또는 pipx로 설치 (격리된 환경)
pipx install scholar-translator
```

**옵션 B: 개발 설치 (기여자용)**
```bash
# 클론 및 편집 가능 모드로 설치
git clone https://github.com/hi-space/paper-pdf-translator.git
cd paper-pdf-translator
pip install -e .

# 또는 uv로
uv sync
```

### 1. MCP Server 직접 시작

**STDIO 모드:**
```bash
scholar-translator --mcp
```

**SSE 모드:**
```bash
scholar-translator --mcp --sse --host 127.0.0.1 --port 3001
```

### 2. 사용 가능한 MCP Tools

- `translate_pdf`: 다양한 옵션으로 PDF 파일 번역
- `analyze_pdf`: 번역 없이 PDF 구조 분석
- `configure_service`: 번역기 서비스 설정 업데이트

### 3. 사용 가능한 MCP Resources

- `config://services`: 사용 가능한 번역 서비스 목록
- `config://models/{service}`: 서비스별 모델 목록
- `config://languages`: 지원되는 언어 코드 목록

### 4. Claude Desktop 통합

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "scholar-translator": {
      "command": "scholar-translator",
      "args": ["--mcp"]
    }
  }
}
```

**참고:** 위의 방법 중 하나를 사용하여 패키지를 전역으로 설치했다고 가정합니다.

### 문제 해결

**"scholar-translator: command not found"**

패키지가 설치되지 않았거나 PATH에 없습니다. 사전 요구사항에서 설치 명령 중 하나를 실행하세요.

**"AWS Credentials Not Found"**

환경 변수 또는 `~/.aws/credentials`에 AWS 인증 정보를 설정하세요:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-west-2"
```

</details>

<details>
  <summary>3.2.5 문제 해결</summary>

**의존성 해결 문제:**

pip로 의존성 충돌이 발생하는 경우:

```bash
# uv 사용 (권장)
uv sync

# 또는 pip로 특정 Python 버전 사용
python3.12 -m pip install -e .
```

**모델 다운로드 문제:**

DocLayout-YOLO 모델 다운로드에 네트워크 문제가 있는 경우:

```bash
# HuggingFace 미러 사용
export HF_ENDPOINT=https://hf-mirror.com
uv run scholar-translator document.pdf
```

**AWS Bedrock 문제:**

Bedrock이 실패하면 Google Translate를 대안으로 사용:

```bash
uv run scholar-translator document.pdf -s google
```

**Python 버전 문제:**

Python 3.10-3.12를 사용하고 있는지 확인 (3.13은 아직 완전히 지원되지 않음):

```bash
python --version

# uv로 (자동으로 Python 버전 관리)
uv python install 3.12
uv python pin 3.12
```

</details>

<details>
  <summary>3.2.6 대안: pip 설치</summary>

`uv`를 사용할 수 없는 경우 `pip`로 설치할 수 있습니다:

**PyPI에서 (출시 시):**
```bash
pip install scholar-translator
```

**소스에서:**
```bash
git clone https://github.com/hi-space/paper-pdf-translator.git
cd paper-pdf-translator
python3.12 -m pip install -e .
```

**참고:** 더 나은 의존성 관리와 빠른 성능을 위해 `uv`가 권장 설치 방법입니다.

</details>


<h2 id="usage">4. 사용 가이드</h2>

### 4.1 기본 사용법

번역을 실행하여 두 개의 PDF 파일이 있는 언어별 하위 폴더를 생성합니다:

```bash
scholar-translator document.pdf -lo ko
```

**출력 구조:**
```
./document-ko/
  ├── document-ko-mono.pdf  # 번역만
  └── document-ko-dual.pdf  # 이중 언어 (원본 + 번역)
```

- `{filename}-{lang}-mono.pdf`: 번역된 텍스트만 (기본값: 한국어)
- `{filename}-{lang}-dual.pdf`: 이중 언어 (원본 + 번역된 텍스트)
- 출력 하위 폴더: `{filename}-{lang}/` (예: 한국어 번역의 경우 `document-ko/`)

**다국어 번역:**
```bash
scholar-translator document.pdf -lo ko  # document-ko/ 하위 폴더 생성
scholar-translator document.pdf -lo ja  # document-ja/ 하위 폴더 생성
```

**여러 언어의 출력 구조:**
```
./document-ko/
  ├── document-ko-mono.pdf
  └── document-ko-dual.pdf
./document-ja/
  ├── document-ja-mono.pdf
  └── document-ja-dual.pdf
```

**기본 동작:**
- 소스 언어: 자동 감지
- 대상 언어: 한국어
- 번역 서비스: AWS Bedrock (Claude Haiku 4.5)
- 출력: 언어별 하위 폴더 자동 생성

### 4.2 커맨드 라인 옵션

| 옵션                  | 기능                              | 예제                                              |
| --------------------- | --------------------------------- | ------------------------------------------------- |
| `files`               | 로컬 PDF 파일                     | `scholar-translator document.pdf`               |
| `-i`                  | GUI 실행                          | `scholar-translator -i`                         |
| `-li`                 | 소스 언어 (기본값: auto)          | `scholar-translator doc.pdf -li en`             |
| `-lo`                 | 대상 언어 (기본값: ko)            | `scholar-translator doc.pdf -lo ja`             |
| `-s`                  | 번역 서비스                       | `scholar-translator doc.pdf -s google`          |
| `-m`                  | 모델 이름/단축키                  | `scholar-translator doc.pdf -m haiku`           |
| `-t`                  | 스레드 수 (기본값: 4)             | `scholar-translator doc.pdf -t 8`               |
| `-o`                  | 출력 디렉토리                     | `scholar-translator doc.pdf -o output/`         |
| `-p`                  | 페이지 범위                       | `scholar-translator doc.pdf -p 1-5`             |
| `-f`                  | 수식 감지용 폰트 정규식           | `scholar-translator doc.pdf -f "(MS.*)"`        |
| `-c`                  | 수식 감지용 문자 정규식           | `scholar-translator doc.pdf -c "[0-9]"`         |
| `--ignore-cache`      | 번역 캐시 비활성화                | `scholar-translator doc.pdf --ignore-cache`     |
| `--skip-subset-fonts` | 폰트 서브셋팅 건너뛰기            | `scholar-translator doc.pdf --skip-subset-fonts`|
| `--config`            | 설정 파일 로드                    | `scholar-translator --config config.json`       |
| `--mcp`               | MCP 서버 시작 (STDIO)             | `scholar-translator --mcp`                      |
| `--mcp --sse`         | MCP 서버 시작 (SSE)               | `scholar-translator --mcp --sse --port 3001`    |

### 4.3 번역 서비스

| 서비스    | 설명                             | 필요한 환경 변수                                  |
| --------- | -------------------------------- | ------------------------------------------------- |
| `bedrock` | AWS Bedrock (Claude 4.5) - 기본  | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`      |
| `google`  | Google Translate - 무료          | 없음                                              |

### 4.4 지원 언어

| 언어                | 코드    |
| ------------------- | ------- |
| 한국어              | `ko`    |
| 영어                | `en`    |
| 일본어              | `ja`    |
| 프랑스어            | `fr`    |
| 독일어              | `de`    |
| 스페인어            | `es`    |
| 러시아어            | `ru`    |
| 이탈리아어          | `it`    |

### 4.5 Python API

Python 애플리케이션에서 **Scholar Translator**를 사용하세요:

**설치:**
```bash
# 권장: uv로
uv sync

# 대안: PyPI에서 (출시 시)
pip install scholar-translator
```

```python
from scholar_translator import translate, translate_stream

# 파일 번역
params = {
    'lang_in': 'en',
    'lang_out': 'ko',
    'service': 'bedrock',
    'model': 'sonnet',
    'thread': 4
}

# 로컬 파일 번역
# 생성된 PDF 경로 반환: ('example-ko/example-ko-mono.pdf', 'example-ko/example-ko-dual.pdf')
# 참고: 언어별 하위 폴더 'example-ko/'를 자동으로 생성
(file_mono, file_dual) = translate(files=['example.pdf'], **params)[0]

# 바이트에서 번역
with open('example.pdf', 'rb') as f:
    (stream_mono, stream_dual) = translate_stream(stream=f.read(), **params)

    # 출력 수동 저장
    with open('output-mono.pdf', 'wb') as out:
        out.write(stream_mono)
    with open('output-dual.pdf', 'wb') as out:
        out.write(stream_dual)
```

**출력 구조:**
- `translate()` 함수는 언어별 하위 폴더를 자동으로 생성: `{filename}-{lang_out}/`
- 출력 파일에는 언어 코드 포함: `{filename}-{lang_out}-mono.pdf` 및 `{filename}-{lang_out}-dual.pdf`
- `translate_stream()` 함수는 어디든 저장할 수 있는 바이트를 반환


### 4.6 Model Context Protocol (MCP) 통합

**Scholar Translator**는 AI 어시스턴트와 함께 MCP 서버로 사용할 수 있습니다.

**설치:**
```bash
# 권장: uv로
uv sync

# 대안: PyPI에서 (출시 시)
pip install scholar-translator
```

**사용법:**

```python
from scholar_translator.mcp_server import create_mcp_app

# MCP 애플리케이션 생성
mcp = create_mcp_app()

# 사용 가능한 도구:
# - translate_pdf(file, lang_in, lang_out, service, model, thread)
# - analyze_pdf(file)
# - configure_service(service, config)

# 사용 가능한 리소스:
# - config://services
# - config://models/{service}
# - config://languages
```

<h2 id="information">5. 프로젝트 정보</h2>

### 5.1 이 프로젝트에 대하여

**Scholar Translator**는 [PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)의 포크로, AWS Bedrock 통합과 함께 한국어 번역에 최적화되었습니다.

**원본 프로젝트 인용:**

원본 PDFMathTranslate는 [EMNLP 2025](https://aclanthology.org/2025.emnlp-demos.71/)에 수록되었습니다:

```bibtex
@inproceedings{ouyang-etal-2025-pdfmathtranslate,
    title = "{PDFM}ath{T}ranslate: Scientific Document Translation Preserving Layouts",
    author = "Ouyang, Rongxin and Chu, Chang and Xin, Zhikuang and Ma, Xiangyao",
    booktitle = "Proceedings of EMNLP 2025: System Demonstrations",
    year = "2025",
    url = "https://aclanthology.org/2025.emnlp-demos.71/"
}
```
### 5.2 감사의 말

**Scholar Translator**는 훌륭한 오픈소스 프로젝트를 기반으로 구축되었습니다:

#### 핵심 기술
- **[PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)**: 원본 프로젝트 기반
- **[AWS Bedrock](https://aws.amazon.com/bedrock/)**: Claude 4.5 Sonnet 번역 엔진
- **[PyMuPDF](https://github.com/pymupdf/PyMuPDF)**: PDF 문서 조작
- **[Pdfminer.six](https://github.com/pdfminer/pdfminer.six)**: PDF 파싱 및 텍스트 추출

#### AI & 레이아웃 감지
- **[DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)**: 문서 레이아웃 감지
- **[Anthropic Claude](https://www.anthropic.com/)**: 최첨단 언어 모델

#### UI & 인프라
- **[Gradio](https://gradio.app/)**: 웹 인터페이스 프레임워크
- **[FastMCP](https://github.com/jlowin/fastmcp)**: Model Context Protocol 구현
- **[Go Noto Universal](https://github.com/satbyy/go-noto-universal)**: 다국어 폰트 지원

### 5.3 라이선스

이 프로젝트는 **AGPL-3.0 라이선스** 하에 라이선스가 부여됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

### 5.4 관련 프로젝트

- **[PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)**: 원본 중국어 중심 버전
- **[PDFMathTranslate-next](https://github.com/PDFMathTranslate/PDFMathTranslate-next)**: 향상된 호환성이 있는 개선된 포크
