#!/bin/bash
# NLLB 번역 모델 다운로드 스크립트

set -e  # Exit on error

# Conda 환경 이름
ENV_NAME="subweave"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "NLLB 번역 모델 다운로드"
echo "=========================================="
echo ""

# Miniconda 설치 확인
if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ Miniconda/Anaconda가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# Conda 환경 존재 확인
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${RED}✗ Conda 환경 '${ENV_NAME}'이 존재하지 않습니다.${NC}"
    echo "먼저 install.sh를 실행해주세요."
    exit 1
fi

# Conda 초기화 및 환경 활성화
echo "Conda 환경 활성화: ${ENV_NAME}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# 모델 저장 경로
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/data/models/nllb-200-distilled-600M"

# 이미 모델이 존재하는지 확인
if [ -f "$MODEL_DIR/model.bin" ]; then
    echo -e "${GREEN}✓ 모델이 이미 설치되어 있습니다${NC}"
    echo "  위치: $MODEL_DIR"
    echo ""
    echo "기존 모델을 삭제하고 다시 다운로드하시겠습니까? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "취소되었습니다."
        exit 0
    fi
    echo "기존 모델 삭제 중..."
    rm -rf "$MODEL_DIR"
fi

# 모델 디렉토리 생성
echo ""
echo "모델 디렉토리 생성 중..."
mkdir -p "$MODEL_DIR"

# ct2-transformers-converter 설치 확인
if ! command -v ct2-transformers-converter &> /dev/null; then
    echo "ct2-transformers-converter 설치 중..."
    pip install ctranslate2 transformers sentencepiece
fi

# NLLB 모델 다운로드 및 변환
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NLLB-200 모델 다운로드 및 변환"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  모델: facebook/nllb-200-distilled-600M"
echo "  출력: $MODEL_DIR"
echo "  양자화: int8 (메모리 절약)"
echo "  크기: ~1.2GB"
echo ""
echo "이 작업은 5-10분 정도 소요될 수 있습니다..."
echo ""

ct2-transformers-converter \
    --model facebook/nllb-200-distilled-600M \
    --output_dir "$MODEL_DIR" \
    --quantization int8 \
    --low_cpu_mem_usage \
    --force

# 변환 성공 확인
if [ -f "$MODEL_DIR/model.bin" ]; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ 모델 다운로드 완료!${NC}"
    echo "=========================================="
    echo ""
    echo "모델 위치: $MODEL_DIR"
    echo ""
    echo "이제 SubWeave를 실행할 수 있습니다:"
    echo "  ./run.sh"
    echo ""
else
    echo ""
    echo -e "${RED}✗ 모델 변환에 실패했습니다.${NC}"
    echo "로그를 확인하고 다시 시도해주세요."
    exit 1
fi
