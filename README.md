# SubWeave - 일본어 동영상 자동 자막 생성기

macOS용 데스크탑 애플리케이션으로, MP4 비디오를 재생하며 일본어 음성을 자동으로 인식하여 한국어 자막을 생성합니다.

## 주요 기능

- **자동 음성 인식 (ASR)**: OpenAI Whisper (오픈소스)를 사용한 정확한 일본어 음성 인식
- **GPU 가속**: Apple Silicon MPS, NVIDIA CUDA 자동 감지 및 활용
- **자동 번역**: CTranslate2 + NLLB-200을 사용한 일본어→한국어 기계 번역
- **통합 비디오 플레이어**: Qt Multimedia 기반의 안정적인 비디오 재생
- **비디오 편집**: 마커 추가/제거 및 마커 위치에서 비디오 분할 (FFmpeg)
- **플레이리스트**: 동영상을 열면 같은 폴더의 모든 동영상이 자동으로 플레이리스트에 추가
- **자막 캐싱**: 생성된 자막을 캐시하여 빠른 재사용
- **파일 관리**: 시청 중 파일을 휴지통으로 이동 가능 (플레이리스트 자동 동기화)
- **자동 재생**: 동영상 종료 시 자동으로 다음 동영상 재생
- **키보드 단축키**: 편리한 키보드 컨트롤
- **드래그 앤 드롭**: 비디오 파일을 창에 드롭하여 즉시 재생

## 시스템 요구사항

- macOS 11.0 (Big Sur) 이상
- Python 3.10 이상
- Miniconda 또는 Anaconda
- FFmpeg (비디오 편집 기능용, 선택사항)
- 최소 8GB RAM (16GB 권장)
- Apple Silicon (M1/M2/M3) 또는 Intel CPU
- GPU 가속 지원: Apple Silicon MPS, NVIDIA CUDA (선택사항)

## 설치 방법

### 통합 설치 스크립트 (권장)

Miniconda가 설치되어 있다면 하나의 스크립트로 모든 설치를 완료할 수 있습니다:

```bash
# 프로젝트 디렉토리로 이동
cd SubWeave

# 통합 설치 스크립트 실행 (모든 것을 자동으로 설정)
./install.sh
```

설치 스크립트는 다음 작업을 수행합니다:
1. Miniconda/Anaconda 확인
2. FFmpeg 설치 확인 (비디오 편집용, 선택사항)
3. Python 3.10 Conda 환경 생성 및 패키지 설치
4. 프로젝트 데이터 디렉토리 생성 (`data/`)
5. NLLB 번역 모델 다운로드 (선택사항, ~1.2GB, 5-10분 소요)
6. GPU 가속 지원 확인

### 모델만 별도 다운로드

번역 모델을 나중에 다운로드하려면:

```bash
./setup_model.sh
```

## 사용 방법

### 애플리케이션 실행

```bash
./run.sh
```

**비디오 파일과 함께 실행:**
```bash
./run.sh /path/to/video.mp4
```

**또는 직접 실행:**
```bash
conda activate subweave
python main.py
```

### 비디오 파일 열기

1. **File → Open Video...** 메뉴를 선택하거나 `Cmd+O`를 누름
2. MP4 파일 선택
3. 자막이 캐시되어 있지 않으면 자동으로 생성 시작
4. 진행 상황 다이얼로그에서 ASR 및 번역 진행 상황 확인

### 키보드 단축키

#### 재생 컨트롤
| 단축키 | 기능 |
|--------|------|
| `Space` | 재생/일시정지 |
| `Ctrl+.` | 정지 |
| `F` | 전체화면 토글 |
| `←` | 5초 뒤로 이동 |
| `→` | 5초 앞으로 이동 |

#### 자막 컨트롤
| 단축키 | 기능 |
|--------|------|
| `S` | 자막 표시/숨김 토글 |
| `G` | 자막 생성/재생성 |
| `Ctrl+=` | 자막 크기 증가 |
| `Ctrl+-` | 자막 크기 감소 |

#### 비디오 편집
| 단축키 | 기능 |
|--------|------|
| `M` | 현재 위치에 마커 추가 |
| `Shift+M` | 가장 가까운 마커 제거 |
| `Ctrl+K` | 마커 위치에서 비디오 분할 |

#### 플레이리스트
| 단축키 | 기능 |
|--------|------|
| `N` | 다음 비디오 재생 |
| `P` | 이전 비디오 재생 |
| `L` | 플레이리스트 표시/숨김 |

#### 파일 관리
| 단축키 | 기능 |
|--------|------|
| `Delete` 또는 `Backspace` | 현재 비디오 휴지통으로 이동 |
| `Cmd+O` | 비디오 파일 열기 |

#### 기타
| 단축키 | 기능 |
|--------|------|
| `Ctrl+M` | 음소거/해제 |
| `Cmd+Q` | 애플리케이션 종료 |

### 플레이리스트 사용법

1. 비디오 파일을 열면 같은 폴더의 모든 비디오가 자동으로 플레이리스트에 추가됩니다
2. 플레이리스트에서 비디오를 더블클릭하여 재생
3. 현재 재생 중인 비디오는 굵은 글씨로 강조 표시
4. 비디오 종료 시 자동으로 다음 비디오 재생 (설정에서 변경 가능)
5. 플레이리스트 아이템 우클릭으로 컨텍스트 메뉴 사용

## 프로젝트 구조

```
SubWeave/
├── core/
│   ├── config.py              # 설정 관리
│   └── cache_manager.py       # 캐시 관리
├── asr/
│   └── asr_engine.py          # OpenAI Whisper 음성 인식 엔진
├── translation/
│   └── translation_engine.py  # NLLB 번역 엔진
├── subtitle/
│   ├── subtitle_builder.py    # SRT 파일 생성
│   └── subtitle_pipeline.py   # ASR→Translation→SRT 파이프라인
├── player/
│   └── player_widget.py       # Qt Multimedia 플레이어 위젯
├── gui/
│   ├── main_window.py         # 메인 윈도우
│   ├── progress_dialog.py     # 진행 상황 다이얼로그
│   └── playlist_widget.py     # 플레이리스트 위젯
├── utils/
│   ├── file_utils.py          # 파일 관리 유틸리티
│   ├── device_utils.py        # GPU/CPU 감지 유틸리티
│   └── video_editor.py        # 비디오 편집 유틸리티
├── data/                      # 프로젝트 로컬 데이터 디렉토리
│   ├── models/                # 번역 모델
│   ├── cache/                 # 자막 캐시
│   ├── subs/                  # 생성된 자막 파일
│   └── logs/                  # 로그 파일
├── install.sh                 # 통합 설치 스크립트
├── run.sh                     # 실행 스크립트
├── setup_model.sh             # 모델 다운로드 스크립트
├── build.sh                   # macOS 앱 빌드 스크립트
├── main.py                    # 애플리케이션 엔트리포인트
└── requirements.txt           # Python 패키지 의존성
```

## 설정 파일

설정 및 데이터는 프로젝트 디렉토리 내 `data/` 폴더에 저장됩니다:

```
SubWeave/data/
├── config.json                # 애플리케이션 설정
├── models/                    # 번역 모델 (NLLB-200)
│   └── nllb-200-distilled-600M/
├── cache/                     # 자막 캐시
├── subs/                      # 생성된 SRT 파일
└── logs/                      # 애플리케이션 로그
```

설정 파일 (`data/config.json`) 예시:
```json
{
  "asr": {
    "model_size": "medium",
    "device": "auto",
    "language": "ja"
  },
  "translation": {
    "model_name": "nllb-200-distilled-600M",
    "source_lang": "jpn_Jpan",
    "target_lang": "kor_Hang",
    "beam_size": 4,
    "batch_size": 32
  }
}
```

## 문제 해결

### FFmpeg를 찾을 수 없음

비디오 분할 기능을 사용하려면 FFmpeg가 필요합니다:

```bash
brew install ffmpeg
```

### 번역 모델을 찾을 수 없음

번역 모델이 올바른 위치에 있는지 확인:

```bash
ls data/models/nllb-200-distilled-600M/
```

모델을 다운로드하지 않았다면:

```bash
./setup_model.sh
```

### GPU 가속이 작동하지 않음

**Apple Silicon (M1/M2/M3):**
```bash
# PyTorch가 MPS를 지원하는지 확인
python -c "import torch; print(torch.backends.mps.is_available())"
```

**NVIDIA GPU:**
```bash
# CUDA가 사용 가능한지 확인
python -c "import torch; print(torch.cuda.is_available())"
```

### 메모리 부족

`data/config.json`에서 더 작은 모델 사용:
- ASR: `small`, `base`, 또는 `tiny` 모델
- Translation: distilled 600M 모델 (기본값)

예시:
```json
{
  "asr": {
    "model_size": "small",
    "device": "cpu"
  }
}
```

### Conda 환경 문제

환경을 완전히 재설치:

```bash
conda env remove -n subweave
./install.sh
```

## 빌드 (PyInstaller)

macOS .app 번들 생성:

```bash
./build.sh
```

생성된 앱은 `dist/SubWeave.app`에 위치합니다.

**참고:**
- 번역 모델은 앱에 포함되지 않으며, 앱 실행 후 별도 다운로드 필요
- FFmpeg는 시스템에 설치되어 있어야 함
- Apple Silicon에서 빌드 시 Rosetta 없이 네이티브 실행

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

GitHub: https://github.com/blue-code/SubWeave

## 참고 자료

### AI 모델 & 엔진
- [OpenAI Whisper](https://github.com/openai/whisper) - 오픈소스 음성 인식
- [CTranslate2](https://opennmt.net/CTranslate2/) - 빠른 추론 엔진
- [NLLB-200](https://github.com/facebookresearch/fairseq/tree/nllb) - Meta의 다국어 번역 모델

### 프레임워크
- [PySide6](https://doc.qt.io/qtforpython/) - Qt for Python
- [Qt Multimedia](https://doc.qt.io/qt-6/qtmultimedia-index.html) - 비디오 재생
- [FFmpeg](https://ffmpeg.org/) - 비디오 처리

### 유틸리티
- [Send2Trash](https://github.com/arsenetar/send2trash) - 안전한 파일 삭제
- [PyTorch](https://pytorch.org/) - MPS/CUDA GPU 가속
