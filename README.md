<img src="./peng.jpg" width="200" height="200"/>

# Keyboard Sound Tune

키보드 입력 시 소리를 재생하는 프로그램입니다. 한글과 영어 입력 모두 지원합니다.

## 기능

- 키보드 입력 시 소리 재생
- 한글/영어 입력 모드 자동 감지
- 시스템 트레이 아이콘 지원
- 소리 ON/OFF 토글 기능

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install pygame keyboard pywin32 PyQt5 psutil
```

2. 프로그램 실행:
```bash
python main.py
```

## 사용 방법

1. 프로그램 실행 후 시스템 트레이에 아이콘이 표시됩니다.
2. "소리 ON" 버튼을 클릭하여 키보드 소리를 활성화합니다.
3. 키보드를 입력하면 해당하는 소리가 재생됩니다.
4. 시스템 트레이 아이콘을 통해 소리를 켜고 끌 수 있습니다.

## 파일 구조

- `main.py`: 메인 프로그램 파일
- `sound_ui.py`: UI 관련 코드
- `sound_ui.ui`: UI 디자인 파일
- `sounds/`: 소리 파일 디렉토리
  - 한글 자음/모음 소리 파일
  - 영문 키 소리 파일

## 라이선스

MIT License 
