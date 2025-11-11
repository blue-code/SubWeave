# SubWeave - 일본어 동영상 자동 자막 생성기

macOS용 데스크탑 애플리케이션으로, MP4 비디오를 재생하며 일본어 음성을 자동으로 인식하여 한국어 자막을 생성합니다.

## 주요 기능

- **자동 음성 인식 (ASR)**: faster-whisper를 사용한 정확한 일본어 음성 인식
- **자동 번역**: CTranslate2 + NLLB-200을 사용한 일본어→한국어 기계 번역
- **통합 비디오 플레이어**: libmpv 기반의 고성능 비디오 플레이어
- **플레이리스트**: 동영상을 열면 같은 폴더의 모든 동영상이 자동으로 플레이리스트에 추가
- **자막 캐싱**: 생성된 자막을 캐시하여 빠른 재사용
- **파일 관리**: 시청 중 파일을 휴지통으로 이동 가능
- **자동 재생**: 동영상 종료 시 자동으로 다음 동영상 재생
- **키보드 단축키**: 편리한 키보드 컨트롤

## 시스템 요구사항

- macOS 11.0 (Big Sur) 이상
- Python 3.9 이상
- Homebrew (libmpv 설치용)
- 최소 8GB RAM (16GB 권장)
- Apple Silicon (M1/M2) 또는 Intel CPU

## 설치 방법

### Miniconda 사용 (권장)

Miniconda가 설치되어 있는 경우 가장 간단한 방법입니다:

```bash
# 프로젝트 디렉토리로 이동
cd subweave

# 1. 자동 설치 스크립트 실행
./install_conda.sh

# 2. NLLB 번역 모델 설정 (약 5-10분 소요)
./setup_model_conda.sh

# 3. 애플리케이션 실행
./run_conda.sh
```

완료! 이제 SubWeave를 사용할 수 있습니다.

## 사용 방법

### 애플리케이션 실행

```bash
./run_conda.sh
```

**비디오 파일과 함께 실행:**
```bash
./run_conda.sh /path/to/video.mp4
```

### 비디오 파일 열기

1. **File → Open Video...** 메뉴를 선택하거나 `Cmd+O`를 누름
2. MP4 파일 선택
3. 자막이 캐시되어 있지 않으면 자동으로 생성 시작
4. 진행 상황 다이얼로그에서 ASR 및 번역 진행 상황 확인

### 키보드 단축키

| 단축키 | 기능 |
|--------|------|
| `Space` | 재생/일시정지 |
| `F` | 전체화면 토글 |
| `S` | 자막 표시/숨김 토글 |
| `Cmd+=` | 자막 크기 증가 |
| `Cmd+-` | 자막 크기 감소 |
| `←` | 5초 뒤로 이동 |
| `→` | 5초 앞으로 이동 |
| `N` | 다음 비디오 재생 |
| `P` | 이전 비디오 재생 |
| `L` | 플레이리스트 표시/숨김 |
| `D` | 현재 비디오 휴지통으로 이동 |
| `Cmd+O` | 비디오 파일 열기 |
| `Cmd+Q` | 애플리케이션 종료 |

### 플레이리스트 사용법

1. 비디오 파일을 열면 같은 폴더의 모든 비디오가 자동으로 플레이리스트에 추가됩니다
2. 플레이리스트에서 비디오를 더블클릭하여 재생
3. 현재 재생 중인 비디오는 굵은 글씨로 강조 표시
4. 비디오 종료 시 자동으로 다음 비디오 재생 (설정에서 변경 가능)
5. 플레이리스트 아이템 우클릭으로 컨텍스트 메뉴 사용

## 프로젝트 구조

```
subweave/
├── core/
│   ├── config.py           # 설정 관리
│   └── cache_manager.py    # 캐시 관리
├── asr/
│   └── asr_engine.py       # Whisper 음성 인식 엔진
├── translation/
│   └── translation_engine.py  # NLLB 번역 엔진
├── subtitle/
│   ├── subtitle_builder.py    # SRT 파일 생성
│   └── subtitle_pipeline.py   # ASR→Translation→SRT 파이프라인
├── player/
│   └── player_widget.py    # MPV 플레이어 위젯
├── gui/
│   ├── main_window.py      # 메인 윈도우
│   └── progress_dialog.py  # 진행 상황 다이얼로그
├── utils/
│   └── file_utils.py       # 파일 관리 유틸리티
└── main.py                 # 애플리케이션 엔트리포인트
```

## 설정 파일

설정은 다음 위치에 저장됩니다:
```
~/Library/Application Support/SubWeave/config.json
```

캐시 및 자막 파일:
```
~/Library/Application Support/SubWeave/cache/
~/Library/Application Support/SubWeave/subs/
```

## 문제 해결

### libmpv를 찾을 수 없음

```bash
brew install mpv
```

### faster-whisper 설치 오류

Apple Silicon Mac에서는 다음과 같이 설치:
```bash
pip install faster-whisper --no-binary :all:
```

### 번역 모델을 찾을 수 없음

번역 모델이 올바른 위치에 있는지 확인:
```bash
ls ~/Library/Application\ Support/SubWeave/models/
```

### 메모리 부족

`config.json`에서 더 작은 모델 사용:
- ASR: `small` 또는 `base` 모델
- Translation: distilled 600M 모델

## 빌드 (PyInstaller)

macOS .app 번들 생성:

```bash
# 빌드 스크립트 실행
chmod +x build.sh
./build.sh
```

생성된 앱은 `dist/SubWeave.app`에 위치합니다.

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 참고

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [CTranslate2](https://opennmt.net/CTranslate2/)
- [NLLB-200](https://github.com/facebookresearch/fairseq/tree/nllb)
- [python-mpv](https://github.com/jaseg/python-mpv)
- [PySide6](https://doc.qt.io/qtforpython/)
