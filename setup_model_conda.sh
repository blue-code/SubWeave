#!/bin/bash
# NLLB 번역 모델 다운로드 및 변환 스크립트 (Miniconda)

set -e  # Exit on error

# Conda 환경 이름
ENV_NAME="subweave"

echo "=========================================="
echo "NLLB 번역 모델 설정"
echo "=========================================="
echo ""

# Miniconda 설치 확인
if ! command -v conda &> /dev/null; then
    echo "Error: Miniconda/Anaconda가 설치되어 있지 않습니다."
    exit 1
fi

# Conda 환경 존재 확인
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "Error: Conda 환경 '${ENV_NAME}'이 존재하지 않습니다."
    echo "먼저 install_conda.sh를 실행하여 환경을 설치해주세요."
    exit 1
fi

# Conda 초기화 및 환경 활성화
echo "Conda 환경 활성화 중: ${ENV_NAME}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# 모델 저장 경로
MODEL_DIR="$HOME/Library/Application Support/SubWeave/models/nllb-200-distilled-600M"

# 이미 모델이 존재하는지 확인
if [ -d "$MODEL_DIR" ]; then
    # 디렉토리가 존재하는지 확인
    if [ -f "$MODEL_DIR/model.bin" ]; then
        echo "모델이 이미 완전히 설치되어 있습니다: $MODEL_DIR"
        echo "기존 모델을 삭제하고 다시 다운로드하시겠습니까? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "모델 설정을 건너뜁니다."
            exit 0
        fi
        echo "기존 모델 삭제 중..."
        rm -rf "$MODEL_DIR"
    else
        echo "불완전한 모델 디렉토리 발견. 정리 중..."
        rm -rf "$MODEL_DIR"
    fi
fi

# 모델 디렉토리 생성
echo ""
echo "모델 디렉토리 생성 중..."
mkdir -p "$MODEL_DIR"

# ct2-transformers-converter 설치 확인
if ! command -v ct2-transformers-converter &> /dev/null; then
    echo "ct2-transformers-converter가 설치되어 있지 않습니다."
    echo "설치하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        pip install ctranslate2 transformers sentencepiece
    else
        echo "Error: ct2-transformers-converter가 필요합니다."
        exit 1
    fi
fi

# NLLB 모델 다운로드 및 변환
echo ""
echo "=========================================="
echo "NLLB-200 모델 다운로드 및 변환 시작"
echo "=========================================="
echo ""
echo "모델: facebook/nllb-200-distilled-600M"
echo "출력 경로: $MODEL_DIR"
echo "양자화: int8 (메모리 절약)"
echo ""
echo "이 작업은 시간이 걸릴 수 있습니다 (약 5-10분)..."
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
    echo "모델 설정 완료!"
    echo "=========================================="
    echo ""
    echo "모델 위치: $MODEL_DIR"
    echo ""
    echo "이제 SubWeave를 실행할 수 있습니다:"
    echo "  ./run_conda.sh"
    echo ""
else
    echo ""
    echo "Error: 모델 변환에 실패했습니다."
    echo "로그를 확인하고 다시 시도해주세요."
    exit 1
fi
