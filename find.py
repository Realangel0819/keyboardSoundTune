import ctypes
import time
from ctypes import wintypes
import threading
import os
import sys

# 현재 작업 디렉토리 출력
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"Python 실행 경로: {sys.executable}")

# Windows API 상수 정의
KOREAN_LAYOUT = 0x412  # 한국어
ENGLISH_LAYOUT = 0x409  # 영어 (미국) 

# Windows API 타입 정의
wintypes.ULONG_PTR = wintypes.WPARAM

# Windows API 함수 로드
user32 = ctypes.WinDLL("User32.dll", use_last_error=True)

# 한글 키 가상 키 코드
VK_HANGUL = 0x15

# 입력 구조체 정의
class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))

def get_hangul_state():
    """한글 키의 현재 상태를 반환"""
    return user32.GetKeyState(VK_HANGUL)

def change_input_state():
    """한/영 전환"""
    # 키 누르기
    x = INPUT(type=1, ki=KEYBDINPUT(wVk=VK_HANGUL))
    # 키 떼기
    y = INPUT(type=1, ki=KEYBDINPUT(wVk=VK_HANGUL, dwFlags=2))
    
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    time.sleep(0.05)
    user32.SendInput(1, ctypes.byref(y), ctypes.sizeof(y))

def get_current_input_language():
    """현재 입력 언어 상태를 반환"""
    state = get_hangul_state()
    if state == 0:  # 한글 키가 비활성화 상태
        return "영어"
    elif state == 1:  # 한글 키가 활성화 상태
        return "한글"
    else:
        return "알 수 없음"

def check_input_mode():
    """입력 모드를 주기적으로 확인"""
    while True:
        mode = get_current_input_language()
        print(f"현재 입력 모드: {mode}")
        time.sleep(0.1)  # 0.1초마다 확인

if __name__ == "__main__":
    print("프로그램 실행 중... 입력 모드를 확인합니다.")
    print("한/영 키를 눌러보세요.")
    print("0.1초마다 현재 입력 모드가 출력됩니다.")
    
    # 입력 모드 체크를 위한 스레드 시작
    t = threading.Thread(target=check_input_mode)
    t.daemon = True
    t.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
