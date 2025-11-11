#!/bin/bash
# SubWeave Installation Script for Miniconda

set -e  # Exit on error

echo "=========================================="
echo "SubWeave - Miniconda Installation"
echo "=========================================="
echo ""

# Conda 환경 이름
ENV_NAME="subweave"

# Miniconda 설치 확인
if ! command -v conda &> /dev/null; then
    echo "Error: Miniconda/Anaconda가 설치되어 있지 않습니다."
    echo "Miniconda를 먼저 설치해주세요: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
else
    echo "✓ Conda가 설치되어 있습니다"
    conda --version
fi

# Qt Multimedia 사용 - 별도 설치 불필요
echo ""
echo "✓ Qt Multimedia를 사용하여 안정적인 비디오 재생 지원"

# 기존 환경 확인
echo ""
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "Conda 환경 '${ENV_NAME}'이 이미 존재합니다."
    echo "기존 환경을 삭제하고 새로 만드시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "기존 환경 삭제 중..."
        conda env remove -n ${ENV_NAME} -y
    else
        echo "기존 환경을 사용합니다."
        conda activate ${ENV_NAME}
        echo "패키지 업데이트 중..."
        pip install --upgrade pip
        pip install -r requirements.txt --upgrade
        echo ""
        echo "=========================================="
        echo "환경 업데이트 완료!"
        echo "=========================================="
        exit 0
    fi
fi

# Conda 환경 생성
echo ""
echo "Conda 환경 생성 중: ${ENV_NAME}"
conda create -n ${ENV_NAME} python=3.10 -y

# Conda 환경 활성화
echo ""
echo "Conda 환경 활성화 중..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# pip 업그레이드
echo ""
echo "pip 업그레이드 중..."
pip install --upgrade pip

# Python 패키지 설치
echo ""
echo "Python 패키지 설치 중..."
pip install -r requirements.txt

# 모델 디렉토리 생성
echo ""
echo "모델 디렉토리 생성 중..."
mkdir -p ~/Library/Application\ Support/SubWeave/models
mkdir -p ~/Library/Application\ Support/SubWeave/cache
mkdir -p ~/Library/Application\ Support/SubWeave/subs

echo ""
echo "=========================================="
echo "설치 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo ""
echo "1. NLLB 번역 모델 다운로드 및 변환:"
echo "   conda activate ${ENV_NAME}"
echo "   ct2-transformers-converter \\"
echo "       --model facebook/nllb-200-distilled-600M \\"
echo "       --output_dir ~/Library/Application\\ Support/SubWeave/models/nllb-200-distilled-600M \\"
echo "       --quantization int8"
echo ""
echo "2. 애플리케이션 실행:"
echo "   ./run_conda.sh"
echo ""
echo "또는 직접 실행:"
echo "   conda activate ${ENV_NAME}"
echo "   python main.py"
echo ""
