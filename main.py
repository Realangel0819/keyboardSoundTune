import sys
import pygame
import os
import keyboard
import win32api
import win32con
import win32gui
import win32process
import ctypes
from ctypes import wintypes
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QSystemTrayIcon, QMenu, QAction, QStyle, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent, QIcon
from PyQt5.uic import loadUi
import psutil

def find_existing_window():
    """기존에 실행 중인 창을 찾아서 종료"""
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    current_name = current_process.name()
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == current_name and proc.info['pid'] != current_pid:
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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

def force_english_mode():
    """영어 입력 모드로 강제 전환"""
    if get_hangul_state() == 1:  # 한글 모드일 때만 전환
        change_input_state()

class SoundApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # UI 파일 로드
        ui_file = resource_path("sound_ui.ui")
        loadUi(ui_file, self)
        
        pygame.mixer.init()  # Pygame 믹서 초기화

        self.sound_folder = resource_path("sounds")  # 소리 파일이 있는 폴더
        
        # 한글 자음과 영어 키 매핑
        self.kor_consonant_map = {
            'r': 'ㄱ', 's': 'ㄴ', 'e': 'ㄷ', 'f': 'ㄹ', 'a': 'ㅁ',
            'q': 'ㅂ', 't': 'ㅅ', 'd': 'ㅇ', 'w': 'ㅈ', 'z': 'ㅋ',
            'x': 'ㅌ', 'v': 'ㅍ', 'g': 'ㅎ'
        }
        
        # 한글 모음과 영어 키 매핑
        self.kor_vowel_map = {
            'k': 'ㅏ', 'o': 'ㅐ', 'i': 'ㅑ', 'p': 'ㅔ', 'j': 'ㅓ',
            'l': 'ㅣ', 'u': 'ㅕ', 'h': 'ㅗ', 'y': 'ㅛ',
            'n': 'ㅜ', 'b': 'ㅠ', 'm': 'ㅡ', 'c': 'ㅣ'
        }

        # 영문 키보드 소리
        self.eng_sound_files = {
            chr(97 + i): os.path.join(self.sound_folder, f"{chr(65 + i)}.mp3")
            for i in range(26)  # a부터 z까지
        }
        
        # 숫자키 소리 추가
        for i in range(10):
            self.eng_sound_files[str(i)] = os.path.join(self.sound_folder, f"{i}.mp3")
            
        # 특수키 소리 추가
        self.eng_sound_files.update({
            'enter': os.path.join(self.sound_folder, "enter.mp3"),
            'space': os.path.join(self.sound_folder, "space.mp3"),
            '`': os.path.join(self.sound_folder, "pengsound.mp3")
        })

        self.soundButton.clicked.connect(self.toggle_sound)  # 버튼 연결
        self.sound_on = False

        # 입력 상태 표시 레이블 추가
        self.input_state_label = QLabel("입력 상태: 영어", self)
        self.input_state_label.setStyleSheet("QLabel { color: blue; font-size: 12pt; }")
        self.input_state_label.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.input_state_label)

        # 상태 업데이트 타이머 설정 (10ms마다 업데이트)
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.update_input_state)
        self.state_timer.start(10)  # 10ms마다 업데이트

        # 시스템 트레이 아이콘 설정
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = resource_path("PENG.JPG")
        self.tray_icon.setIcon(QIcon(icon_path))
        
        # 트레이 아이콘 클릭 이벤트 연결
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 트레이 아이콘 메뉴
        tray_menu = QMenu(self)
        
        # 메뉴 항목 설정
        toggle_action = QAction("소리 ON/OFF", self)
        toggle_action.triggered.connect(self.toggle_sound)
        tray_menu.addAction(toggle_action)
        
        quit_action = QAction("종료", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 창 최소화 시 트레이 아이콘으로 숨기기
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(icon_path))  # 실행 아이콘 설정

        # 전역 키보드 후킹 설정
        keyboard.on_press(self.handle_key_press)
        
        # 초기 상태를 영어로 강제 설정
        force_english_mode()
        
        # 초기 소리 파일 매핑 설정
        self.update_sound_mapping()

    def update_sound_mapping(self):
        """현재 입력 모드에 따라 소리 파일 매핑 업데이트"""
        if self.is_korean_input():
            # 한글 입력 모드일 때는 한글 자음/모음 매핑 사용
            self.sound_files = {}
            for eng_key, kor_char in {**self.kor_consonant_map, **self.kor_vowel_map}.items():
                self.sound_files[eng_key] = os.path.join(self.sound_folder, f"{kor_char}.mp3")
        else:
            # 영어 입력 모드일 때는 영문 키 매핑 사용
            self.sound_files = self.eng_sound_files

    def update_input_state(self):
        """입력 상태를 업데이트하는 함수"""
        state = get_hangul_state()
        if state == 1:  # 한글 키가 활성화 상태
            self.input_state_label.setText("입력 상태: 한글")
            self.input_state_label.setStyleSheet("QLabel { color: red; font-size: 12pt; }")
            self.update_sound_mapping()  # 소리 매핑 업데이트
        else:  # 한글 키가 비활성화 상태
            self.input_state_label.setText("입력 상태: 영어")
            self.input_state_label.setStyleSheet("QLabel { color: blue; font-size: 12pt; }")
            self.update_sound_mapping()  # 소리 매핑 업데이트

    def is_korean_input(self):
        """현재 한글 입력 상태인지 확인하는 함수"""
        state = get_hangul_state()
        return state == 1  # 한글 키가 활성화 상태면 한글 입력

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # 왼쪽 클릭
            self.show()  # 창 보이기
            self.activateWindow()  # 창을 활성화

    def handle_key_press(self, event):
        """키 입력 처리"""
        if not self.sound_on:
            return
            
        key = event.name.lower()
        if key in self.sound_files:
            sound_file = self.sound_files[key]
            if os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()

    def toggle_sound(self):
        if not self.sound_on:
            self.soundButton.setText("소리 OFF")
            self.sound_on = True
        else:
            pygame.mixer.music.stop()  # 소리 멈추기
            self.soundButton.setText("소리 ON")
            self.sound_on = False

    def closeEvent(self, event):
        # 창을 닫을 때 트레이 아이콘만 숨기고 프로그램 종료 안함
        event.ignore()
        self.hide()

    def quit_app(self):
        pygame.mixer.music.stop()  # 소리 중지
        keyboard.unhook_all()  # 키보드 후킹 해제
        self.tray_icon.hide()  # 트레이 아이콘 숨기기
        QApplication.quit()  # 애플리케이션 종료


if __name__ == "__main__":
    # 기존 프로그램 찾아서 종료
    find_existing_window()
    
    app = QApplication(sys.argv)
    window = SoundApp()
    window.setWindowTitle("키보드 소리 재생")
    window.show()
    sys.exit(app.exec_())
