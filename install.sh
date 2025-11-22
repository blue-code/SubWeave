#!/bin/bash
# SubWeave 통합 설치 스크립트

set -e  # Exit on error

echo "=========================================="
echo "SubWeave - 일본어→한국어 자막 생성기"
echo "통합 설치 스크립트"
echo "=========================================="
echo ""

# Conda 환경 이름
ENV_NAME="subweave"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Miniconda 설치 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1단계: Miniconda/Anaconda 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ Miniconda/Anaconda가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "Miniconda를 먼저 설치해주세요:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    echo ""
    echo "macOS Intel: https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
    echo "macOS M1/M2: https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    exit 1
else
    echo -e "${GREEN}✓ Conda가 설치되어 있습니다${NC}"
    conda --version
fi

# 2. FFmpeg 설치 확인
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2단계: FFmpeg 확인 (비디오 편집용)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠ FFmpeg가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "FFmpeg는 비디오 분할 기능에 필요합니다."
    echo "Homebrew로 설치하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if command -v brew &> /dev/null; then
            brew install ffmpeg
            echo -e "${GREEN}✓ FFmpeg 설치 완료${NC}"
        else
            echo -e "${RED}✗ Homebrew가 설치되어 있지 않습니다.${NC}"
            echo "수동으로 설치해주세요: https://ffmpeg.org/download.html"
        fi
    else
        echo -e "${YELLOW}⚠ FFmpeg 없이 계속합니다 (비디오 분할 기능 비활성화)${NC}"
    fi
else
    echo -e "${GREEN}✓ FFmpeg가 설치되어 있습니다${NC}"
    ffmpeg -version | head -n 1
fi

# 3. Conda 환경 설정
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3단계: Conda 환경 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 기존 환경 확인
if conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${YELLOW}Conda 환경 '${ENV_NAME}'이 이미 존재합니다.${NC}"
    echo "선택하세요:"
    echo "  1) 기존 환경 업데이트 (권장)"
    echo "  2) 기존 환경 삭제 후 재설치"
    echo "  3) 취소"
    read -p "선택 (1-3): " choice

    case $choice in
        1)
            echo "기존 환경을 업데이트합니다..."
            source $(conda info --base)/etc/profile.d/conda.sh
            conda activate ${ENV_NAME}
            pip install --upgrade pip
            pip install -r requirements.txt --upgrade
            echo -e "${GREEN}✓ 환경 업데이트 완료${NC}"
            ;;
        2)
            echo "기존 환경 삭제 중..."
            conda env remove -n ${ENV_NAME} -y
            echo "새 환경 생성 중..."
            conda create -n ${ENV_NAME} python=3.10 -y
            source $(conda info --base)/etc/profile.d/conda.sh
            conda activate ${ENV_NAME}
            pip install --upgrade pip
            pip install -r requirements.txt
            echo -e "${GREEN}✓ 환경 재설치 완료${NC}"
            ;;
        3)
            echo "설치를 취소합니다."
            exit 0
            ;;
        *)
            echo -e "${RED}잘못된 선택입니다.${NC}"
            exit 1
            ;;
    esac
else
    # 새 환경 생성
    echo "Conda 환경 생성 중: ${ENV_NAME}"
    conda create -n ${ENV_NAME} python=3.10 -y

    echo "Conda 환경 활성화 중..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate ${ENV_NAME}

    echo "pip 업그레이드 중..."
    pip install --upgrade pip

    echo "Python 패키지 설치 중..."
    pip install -r requirements.txt

    echo -e "${GREEN}✓ Conda 환경 생성 완료${NC}"
fi

# 4. 디렉토리 구조 생성
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4단계: 데이터 디렉토리 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SCRIPT_DIR/data/models"
mkdir -p "$SCRIPT_DIR/data/cache"
mkdir -p "$SCRIPT_DIR/data/subs"
mkdir -p "$SCRIPT_DIR/data/logs"
echo -e "${GREEN}✓ 디렉토리 생성 완료${NC}"

# 5. 번역 모델 설정
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5단계: NLLB 번역 모델 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MODEL_DIR="$SCRIPT_DIR/data/models/nllb-200-distilled-600M"

if [ -f "$MODEL_DIR/model.bin" ]; then
    echo -e "${GREEN}✓ 번역 모델이 이미 설치되어 있습니다${NC}"
    echo "  위치: $MODEL_DIR"
else
    echo "NLLB-200 번역 모델을 다운로드하시겠습니까?"
    echo "  크기: ~1.2GB"
    echo "  소요시간: 약 5-10분"
    echo ""
    read -p "다운로드 (y/n): " response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        # ct2-transformers-converter 확인
        if ! command -v ct2-transformers-converter &> /dev/null; then
            echo "ct2-transformers-converter 설치 중..."
            pip install ctranslate2 transformers sentencepiece
        fi

        echo ""
        echo "모델 다운로드 및 변환 중..."
        echo "잠시만 기다려주세요..."

        ct2-transformers-converter \
            --model facebook/nllb-200-distilled-600M \
            --output_dir "$MODEL_DIR" \
            --quantization int8 \
            --low_cpu_mem_usage \
            --force

        if [ -f "$MODEL_DIR/model.bin" ]; then
            echo -e "${GREEN}✓ 모델 다운로드 완료${NC}"
        else
            echo -e "${RED}✗ 모델 다운로드 실패${NC}"
            echo "나중에 수동으로 다운로드할 수 있습니다:"
            echo "  ./setup_model.sh"
        fi
    else
        echo -e "${YELLOW}⚠ 모델 다운로드를 건너뜁니다${NC}"
        echo ""
        echo "나중에 다운로드하려면:"
        echo "  conda activate ${ENV_NAME}"
        echo "  ct2-transformers-converter \\"
        echo "      --model facebook/nllb-200-distilled-600M \\"
        echo "      --output_dir \"$MODEL_DIR\" \\"
        echo "      --quantization int8"
    fi
fi

# 6. GPU 지원 확인
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6단계: GPU 지원 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# macOS Metal 확인
if [[ "$(uname)" == "Darwin" ]]; then
    if sysctl -n machdep.cpu.brand_string | grep -q "Apple"; then
        echo -e "${GREEN}✓ Apple Silicon 감지 - MPS GPU 가속 사용 가능${NC}"
        echo "  ASR(음성인식)에서 GPU 가속이 활성화됩니다."
    else
        echo "Intel Mac - CPU 사용"
    fi
else
    # NVIDIA GPU 확인
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ NVIDIA GPU 감지 - CUDA 가속 사용 가능${NC}"
    else
        echo "GPU 없음 - CPU 사용"
    fi
fi

# 완료 메시지
echo ""
echo "=========================================="
echo -e "${GREEN}설치 완료!${NC}"
echo "=========================================="
echo ""
echo "SubWeave 실행 방법:"
echo ""
echo "  1. 간단한 방법:"
echo "     ./run.sh"
echo ""
echo "  2. 직접 실행:"
echo "     conda activate ${ENV_NAME}"
echo "     python main.py"
echo ""
echo "주요 기능:"
echo "  • 일본어 음성 인식 (OpenAI Whisper)"
echo "  • 일본어→한국어 번역 (NLLB-200)"
echo "  • 비디오 마커 & 분할 (FFmpeg)"
echo "  • GPU 가속 지원 (Apple MPS, NVIDIA CUDA)"
echo ""
echo "문제가 발생하면:"
echo "  - 로그 확인: data/logs/"
echo "  - GitHub Issues: https://github.com/blue-code/SubWeave/issues"
echo ""
