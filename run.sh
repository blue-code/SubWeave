#!/bin/bash
# SubWeave 실행 스크립트

set -e  # Exit on error

# Conda 환경 이름
ENV_NAME="subweave"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "SubWeave - 일본어→한국어 자막 생성기"
echo "=========================================="
echo ""

# Miniconda 설치 확인
if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ Miniconda/Anaconda가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "먼저 설치 스크립트를 실행해주세요:"
    echo "  ./install.sh"
    exit 1
fi

# Conda 환경 존재 확인
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${RED}✗ Conda 환경 '${ENV_NAME}'이 존재하지 않습니다.${NC}"
    echo ""
    echo "먼저 설치 스크립트를 실행해주세요:"
    echo "  ./install.sh"
    exit 1
fi

# Conda 초기화 및 환경 활성화
echo -e "${GREEN}✓ Conda 환경 활성화: ${ENV_NAME}${NC}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# Python 버전 확인
echo "  Python: $(python --version | cut -d' ' -f2)"

# GPU 정보 표시
if [[ "$(uname)" == "Darwin" ]]; then
    if sysctl -n machdep.cpu.brand_string | grep -q "Apple"; then
        echo -e "  GPU: ${GREEN}Apple Silicon (MPS 가속 활성화)${NC}"
    else
        echo "  GPU: Intel (CPU 사용)"
    fi
elif command -v nvidia-smi &> /dev/null 2>&1; then
    echo -e "  GPU: ${GREEN}NVIDIA CUDA (가속 활성화)${NC}"
else
    echo "  GPU: 없음 (CPU 사용)"
fi

echo ""

# Locale 설정 (UTF-8)
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# 스크립트가 위치한 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 모델 존재 확인
MODEL_DIR="$SCRIPT_DIR/data/models/nllb-200-distilled-600M"
if [ ! -f "$MODEL_DIR/model.bin" ]; then
    echo -e "${YELLOW}⚠ 번역 모델이 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "번역 기능을 사용하려면 모델을 다운로드해야 합니다."
    echo "  ./install.sh 를 다시 실행하거나"
    echo "  수동으로 모델을 다운로드하세요."
    echo ""
fi

# 애플리케이션 실행
echo "SubWeave 시작..."
echo ""

python main.py "$@"
