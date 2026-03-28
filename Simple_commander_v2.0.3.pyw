#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Commander v2.1
파일 관리자 - 듀얼 패널 + 현대적 디자인

개선사항 (v1.07 → v2.1):
  • 현대적 플랫 디자인 (Segoe UI 폰트, 아이콘 개선)
  • 4가지 테마 (라이트·다크·블루·그린)
  • 브레드크럼 경로 탐색바
  • 컬럼 헤더 클릭 정렬 (이름/크기/날짜/종류, 토글)
  • 파일 필터바 (이름/확장자 실시간 필터)
  • 북마크 사이드바 (즐겨찾기 추가·삭제·저장)
  • 디스크 사용량 표시 (상태바)
  • 복사/이동 진행률 다이얼로그
  • 일괄 이름바꾸기 다이얼로그
  • 내장 텍스트 뷰어 (F3, 텍스트/코드 파일)
  • 탭 기능 - 패널별 다중 탭 (Ctrl+T / Ctrl+W)
  • 분할기(Sash) 위치 기억
  • 설정 자동 저장 (settings.json)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os, shutil, json, platform, subprocess, threading, fnmatch
from pathlib import Path
from datetime import datetime

# ─── 플랫폼별 최적 폰트 ────────────────────────────────────────────────────
if platform.system() == 'Windows':
    UI_FONT   = 'Segoe UI'
    MONO_FONT = 'Consolas'
elif platform.system() == 'Darwin':
    UI_FONT   = 'SF Pro Text'
    MONO_FONT = 'Menlo'
else:
    UI_FONT   = 'Ubuntu'
    MONO_FONT = 'Ubuntu Mono'

SETTINGS_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sc_settings.json')
BOOKMARKS_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sc_bookmarks.json')
RECENT_MAX      = 20   # 최근 방문 경로 최대 보관 수

# ─── 테마 정의 ───────────────────────────────────────────────────────────────
THEMES = {
    '라이트': {
        'main_bg':'#F5F6FA', 'panel_bg':'#FFFFFF', 'toolbar_bg':'#EAECF2',
        'toolbar_fg':'#2D3748', 'accent':'#4A90D9', 'accent_fg':'#FFFFFF',
        'border':'#D0D5E0', 'status_bg':'#EAECF2', 'status_fg':'#4A5568',
        'tree_fg':'#2D3748', 'tree_bg':'#FFFFFF', 'tree_alt':'#F7F8FB',
        'tree_head_bg':'#EDF2F7', 'tree_head_fg':'#2D3748',
        'tree_sel_bg':'#4A90D9', 'tree_sel_fg':'#FFFFFF',
        'btn_bg':'#FFFFFF', 'btn_fg':'#2D3748', 'btn_border':'#C5CBD6',
        'bmark_bg':'#F0F2F8', 'bmark_fg':'#2D3748', 'bmark_sel':'#D0E4F7',
        'tab_active':'#FFFFFF', 'tab_inactive':'#E2E6F0', 'tab_fg':'#2D3748',
        'entry_bg':'#FFFFFF', 'entry_fg':'#2D3748',
        'crumb_bg':'#EAECF2', 'crumb_fg':'#4A5568', 'crumb_sep':'#A0AAB8',
        'filter_bg':'#FFFFFF', 'filter_fg':'#2D3748',
    },
    '다크': {
        'main_bg':'#1A1D27', 'panel_bg':'#252836', 'toolbar_bg':'#1F2231',
        'toolbar_fg':'#E2E8F0', 'accent':'#5AA9FA', 'accent_fg':'#1A1D27',
        'border':'#3A3F55', 'status_bg':'#1F2231', 'status_fg':'#A0AEC0',
        'tree_fg':'#E2E8F0', 'tree_bg':'#252836', 'tree_alt':'#2A2D3E',
        'tree_head_bg':'#2D3044', 'tree_head_fg':'#A0AEC0',
        'tree_sel_bg':'#5AA9FA', 'tree_sel_fg':'#1A1D27',
        'btn_bg':'#2D3044', 'btn_fg':'#E2E8F0', 'btn_border':'#3A3F55',
        'bmark_bg':'#1F2231', 'bmark_fg':'#A0AEC0', 'bmark_sel':'#2D3044',
        'tab_active':'#252836', 'tab_inactive':'#1F2231', 'tab_fg':'#E2E8F0',
        'entry_bg':'#2D3044', 'entry_fg':'#E2E8F0',
        'crumb_bg':'#1F2231', 'crumb_fg':'#A0AEC0', 'crumb_sep':'#4A5568',
        'filter_bg':'#2D3044', 'filter_fg':'#E2E8F0',
    },
    '블루': {
        'main_bg':'#EBF2FB', 'panel_bg':'#FFFFFF', 'toolbar_bg':'#1565C0',
        'toolbar_fg':'#FFFFFF', 'accent':'#1976D2', 'accent_fg':'#FFFFFF',
        'border':'#BBDEFB', 'status_bg':'#1565C0', 'status_fg':'#E3F2FD',
        'tree_fg':'#1A237E', 'tree_bg':'#FFFFFF', 'tree_alt':'#E8F4FD',
        'tree_head_bg':'#BBDEFB', 'tree_head_fg':'#0D47A1',
        'tree_sel_bg':'#1976D2', 'tree_sel_fg':'#FFFFFF',
        'btn_bg':'#E3F2FD', 'btn_fg':'#0D47A1', 'btn_border':'#90CAF9',
        'bmark_bg':'#DCEEFB', 'bmark_fg':'#0D47A1', 'bmark_sel':'#BBDEFB',
        'tab_active':'#FFFFFF', 'tab_inactive':'#BBDEFB', 'tab_fg':'#0D47A1',
        'entry_bg':'#FFFFFF', 'entry_fg':'#1A237E',
        'crumb_bg':'#1565C0', 'crumb_fg':'#E3F2FD', 'crumb_sep':'#5C9CD4',
        'filter_bg':'#FFFFFF', 'filter_fg':'#1A237E',
    },
    '그린': {
        'main_bg':'#F0FBF4', 'panel_bg':'#FFFFFF', 'toolbar_bg':'#2E7D32',
        'toolbar_fg':'#FFFFFF', 'accent':'#388E3C', 'accent_fg':'#FFFFFF',
        'border':'#C8E6C9', 'status_bg':'#2E7D32', 'status_fg':'#E8F5E9',
        'tree_fg':'#1B5E20', 'tree_bg':'#FFFFFF', 'tree_alt':'#F1FBF3',
        'tree_head_bg':'#C8E6C9', 'tree_head_fg':'#1B5E20',
        'tree_sel_bg':'#388E3C', 'tree_sel_fg':'#FFFFFF',
        'btn_bg':'#E8F5E9', 'btn_fg':'#1B5E20', 'btn_border':'#A5D6A7',
        'bmark_bg':'#DCEEE0', 'bmark_fg':'#1B5E20', 'bmark_sel':'#C8E6C9',
        'tab_active':'#FFFFFF', 'tab_inactive':'#C8E6C9', 'tab_fg':'#1B5E20',
        'entry_bg':'#FFFFFF', 'entry_fg':'#1B5E20',
        'crumb_bg':'#2E7D32', 'crumb_fg':'#E8F5E9', 'crumb_sep':'#5FAD63',
        'filter_bg':'#FFFFFF', 'filter_fg':'#1B5E20',
    },
}

FILE_ICONS = {
    frozenset(['.jpg','.jpeg','.png','.gif','.bmp','.svg','.ico','.webp']): '🖼',
    frozenset(['.mp3','.wav','.flac','.m4a','.ogg','.aac']): '🎵',
    frozenset(['.mp4','.avi','.mkv','.mov','.wmv','.flv','.webm']): '🎬',
    frozenset(['.zip','.rar','.7z','.tar','.gz','.bz2','.xz']): '📦',
    frozenset(['.txt','.log','.md','.rst','.nfo']): '📄',
    frozenset(['.doc','.docx','.odt','.rtf']): '📝',
    frozenset(['.pdf']): '📕',
    frozenset(['.py','.js','.ts','.java','.cpp','.c','.h','.cs','.go','.rs','.rb','.php']): '💻',
    frozenset(['.html','.htm','.css','.xml','.json','.yaml','.yml','.toml']): '🌐',
    frozenset(['.xlsx','.xls','.csv','.ods']): '📊',
    frozenset(['.ppt','.pptx','.odp']): '📽',
    frozenset(['.exe','.msi','.bat','.sh','.cmd','.app']): '⚙',
    frozenset(['.db','.sqlite','.sql']): '🗃',
    frozenset(['.iso','.img']): '💿',
}

TEXT_EXTS = {'.txt','.log','.md','.py','.js','.ts','.json','.yaml','.yml',
             '.toml','.html','.htm','.css','.xml','.csv','.rst','.ini',
             '.cfg','.conf','.sh','.bat','.c','.cpp','.h','.java','.go',
             '.rb','.php','.rs','.cs','.sql','.nfo','.rtf'}

def get_file_icon(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    for exts, icon in FILE_ICONS.items():
        if ext in exts:
            return icon
    return '📃'

def get_file_type(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    mapping = {
        '.txt':'텍스트','.log':'로그','.md':'Markdown',
        '.pdf':'PDF','.doc':'Word','.docx':'Word',
        '.jpg':'이미지','.jpeg':'이미지','.png':'이미지','.gif':'이미지','.bmp':'이미지',
        '.mp3':'음악','.wav':'음악','.flac':'음악','.m4a':'음악',
        '.mp4':'비디오','.avi':'비디오','.mkv':'비디오','.mov':'비디오',
        '.zip':'ZIP압축','.rar':'RAR압축','.7z':'7Z압축','.tar':'TAR압축','.gz':'GZ압축',
        '.py':'Python','.js':'JavaScript','.ts':'TypeScript','.java':'Java',
        '.cpp':'C++','.c':'C','.cs':'C#','.go':'Go','.rs':'Rust','.rb':'Ruby',
        '.html':'HTML','.htm':'HTML','.css':'CSS',
        '.json':'JSON','.xml':'XML','.yaml':'YAML','.yml':'YAML',
        '.xlsx':'Excel','.xls':'Excel','.csv':'CSV',
        '.ppt':'PowerPoint','.pptx':'PowerPoint',
        '.exe':'실행파일','.msi':'설치파일','.sh':'쉘스크립트','.bat':'배치파일',
        '.db':'데이터베이스','.sqlite':'SQLite',
        '.iso':'디스크이미지',
    }
    return mapping.get(ext, '파일')

# ─── 종류별 색상 카테고리 ─────────────────────────────────────────────────────
# get_file_type() 반환값 → 색상 카테고리 태그
TYPE_CATEGORY = {
    # 이미지
    '이미지':      'cat_image',
    # 음악
    '음악':        'cat_audio',
    # 비디오
    '비디오':      'cat_video',
    # 압축
    'ZIP압축':     'cat_archive',
    'RAR압축':     'cat_archive',
    '7Z압축':      'cat_archive',
    'TAR압축':     'cat_archive',
    'GZ압축':      'cat_archive',
    # 코드
    'Python':      'cat_code',
    'JavaScript':  'cat_code',
    'TypeScript':  'cat_code',
    'Java':        'cat_code',
    'C++':         'cat_code',
    'C':           'cat_code',
    'C#':          'cat_code',
    'Go':          'cat_code',
    'Rust':        'cat_code',
    'Ruby':        'cat_code',
    # 웹/데이터
    'HTML':        'cat_web',
    'CSS':         'cat_web',
    'JSON':        'cat_web',
    'XML':         'cat_web',
    'YAML':        'cat_web',
    # 문서
    'PDF':         'cat_doc',
    'Word':        'cat_doc',
    'PowerPoint':  'cat_doc',
    'Markdown':    'cat_doc',
    '텍스트':      'cat_text',
    '로그':        'cat_text',
    # 스프레드시트
    'Excel':       'cat_sheet',
    'CSV':         'cat_sheet',
    # 실행 파일
    '실행파일':    'cat_exec',
    '설치파일':    'cat_exec',
    '배치파일':    'cat_exec',
    '쉘스크립트':  'cat_exec',
    # 데이터베이스
    '데이터베이스':'cat_db',
    'SQLite':      'cat_db',
    # 디스크
    '디스크이미지':'cat_disk',
}

# 테마별 카테고리 색상 (bg_normal, bg_alt)
TYPE_COLORS = {
    '라이트': {
        'cat_image':   ('#FFF0F5', '#FFE0ED'),  # 분홍
        'cat_audio':   ('#F3EEFF', '#E8DAFF'),  # 연보라
        'cat_video':   ('#FFF4E6', '#FFE8CC'),  # 주황
        'cat_archive': ('#FFFAE6', '#FFF0B3'),  # 노랑
        'cat_code':    ('#E8FFF0', '#D0F5E0'),  # 연초록
        'cat_web':     ('#E6F7FF', '#CCEDFF'),  # 하늘
        'cat_doc':     ('#EEF2FF', '#DDE5FF'),  # 연파랑
        'cat_text':    ('#F5F5FF', '#EAEAFF'),  # 연남색
        'cat_sheet':   ('#EDFFF8', '#D5F5EC'),  # 민트
        'cat_exec':    ('#FFF0EE', '#FFD8D3'),  # 연빨강
        'cat_db':      ('#FFF5E6', '#FFEACC'),  # 살구
        'cat_disk':    ('#F0F0F0', '#E4E4E4'),  # 회색
    },
    '다크': {
        'cat_image':   ('#3D2533', '#36202D'),
        'cat_audio':   ('#2D2540', '#282038'),
        'cat_video':   ('#3D2E1A', '#352818'),
        'cat_archive': ('#383318', '#302D14'),
        'cat_code':    ('#1E3528', '#1A3022'),
        'cat_web':     ('#1C3040', '#182B38'),
        'cat_doc':     ('#1E2B42', '#1A2638'),
        'cat_text':    ('#201E42', '#1C1A3A'),
        'cat_sheet':   ('#1E3530', '#1A3028'),
        'cat_exec':    ('#3D1E1E', '#381A1A'),
        'cat_db':      ('#3A2E1A', '#342818'),
        'cat_disk':    ('#2E2E2E', '#282828'),
    },
    '블루': {
        'cat_image':   ('#FFF0F5', '#FFE0ED'),
        'cat_audio':   ('#F0EAFF', '#E3D8FF'),
        'cat_video':   ('#FFF3E0', '#FFE6C0'),
        'cat_archive': ('#FFFDE6', '#FFF8B8'),
        'cat_code':    ('#E6FFF2', '#CCFFE6'),
        'cat_web':     ('#E0F7FF', '#C0EEFF'),
        'cat_doc':     ('#EEF4FF', '#D8EAFF'),
        'cat_text':    ('#F0F0FF', '#E0E0FF'),
        'cat_sheet':   ('#E6FFEE', '#CEFFDD'),
        'cat_exec':    ('#FFECEC', '#FFD8D8'),
        'cat_db':      ('#FFF3E0', '#FFE6C0'),
        'cat_disk':    ('#F2F2F8', '#E6E6F2'),
    },
    '그린': {
        'cat_image':   ('#FFF0F5', '#FFE0ED'),
        'cat_audio':   ('#F2EEFF', '#E6DAFF'),
        'cat_video':   ('#FFF4E6', '#FFE8CC'),
        'cat_archive': ('#FFFAE6', '#FFF0B3'),
        'cat_code':    ('#E8FFF0', '#D0F5E0'),
        'cat_web':     ('#E6FAFF', '#CCEEFF'),
        'cat_doc':     ('#EEF2FF', '#DDE5FF'),
        'cat_text':    ('#F5F5FF', '#EAEAFF'),
        'cat_sheet':   ('#EDFFF5', '#D5F5E8'),
        'cat_exec':    ('#FFF0EE', '#FFD8D3'),
        'cat_db':      ('#FFF5E6', '#FFEACC'),
        'cat_disk':    ('#F0F2F0', '#E4E8E4'),
    },
}

def get_type_tag(ftype: str, alt: bool) -> str:
    """파일 종류 문자열 → 색상 태그 반환"""
    cat = TYPE_CATEGORY.get(ftype, 'file')
    if cat == 'file':
        return 'file_alt' if alt else 'file'
    return f'{cat}_alt' if alt else cat

def format_size(size: int) -> str:
    for unit in ('B','KB','MB','GB','TB'):
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} PB'

def get_disk_usage(path: str):
    try:
        t = shutil.disk_usage(path)
        return t.total, t.used, t.free
    except Exception:
        return 0, 0, 0


# ─── 내장 텍스트 뷰어 ────────────────────────────────────────────────────────
class TextViewerDialog(tk.Toplevel):
    def __init__(self, parent, file_path: str, theme: dict):
        super().__init__(parent)
        self.title(f'뷰어 — {os.path.basename(file_path)}')
        self.geometry('900x650')
        self.configure(bg=theme['main_bg'])
        self.transient(parent)

        # 툴바
        tb = tk.Frame(self, bg=theme['toolbar_bg'], pady=4)
        tb.pack(fill='x')
        tk.Label(tb, text=f'📄  {file_path}', bg=theme['toolbar_bg'],
                 fg=theme['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left', padx=10)
        tk.Button(tb, text='✕ 닫기', command=self.destroy,
                  bg=theme['accent'], fg=theme['accent_fg'],
                  relief='flat', font=(UI_FONT, 9), padx=10, cursor='hand2').pack(side='right', padx=8)

        # 인코딩 선택
        enc_frame = tk.Frame(tb, bg=theme['toolbar_bg'])
        enc_frame.pack(side='right', padx=8)
        tk.Label(enc_frame, text='인코딩:', bg=theme['toolbar_bg'],
                 fg=theme['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left')
        self._enc_var = tk.StringVar(value='utf-8')
        enc_cb = ttk.Combobox(enc_frame, textvariable=self._enc_var,
                              values=['utf-8','cp949','euc-kr','latin-1','utf-16'],
                              width=9, state='readonly')
        enc_cb.pack(side='left', padx=4)
        enc_cb.bind('<<ComboboxSelected>>', lambda _: self._load(file_path))

        # 텍스트 영역
        frame = tk.Frame(self, bg=theme['panel_bg'])
        frame.pack(fill='both', expand=True, padx=6, pady=6)

        xsb = ttk.Scrollbar(frame, orient='horizontal')
        ysb = ttk.Scrollbar(frame, orient='vertical')
        self._text = tk.Text(frame, wrap='none', font=(MONO_FONT, 10),
                             bg=theme['tree_bg'], fg=theme['tree_fg'],
                             insertbackground=theme['tree_fg'], relief='flat',
                             xscrollcommand=xsb.set, yscrollcommand=ysb.set,
                             state='disabled')
        xsb.config(command=self._text.xview)
        ysb.config(command=self._text.yview)
        ysb.pack(side='right', fill='y')
        xsb.pack(side='bottom', fill='x')
        self._text.pack(fill='both', expand=True)

        # 하단 상태
        self._status = tk.Label(self, text='', anchor='w', padx=8,
                                bg=theme['status_bg'], fg=theme['status_fg'],
                                font=(UI_FONT, 8))
        self._status.pack(fill='x', side='bottom')

        self._file = file_path
        self._load(file_path)

    def _load(self, path):
        enc = self._enc_var.get()
        try:
            with open(path, 'r', encoding=enc, errors='replace') as f:
                content = f.read()
            lines = content.count('\n') + 1
            chars = len(content)
            size  = os.path.getsize(path)
            self._text.config(state='normal')
            self._text.delete('1.0', 'end')
            self._text.insert('1.0', content)
            self._text.config(state='disabled')
            self._status.config(
                text=f'{lines:,}줄  |  {chars:,}자  |  {format_size(size)}  |  인코딩: {enc}')
        except Exception as e:
            self._text.config(state='normal')
            self._text.delete('1.0', 'end')
            self._text.insert('1.0', f'[파일을 읽을 수 없습니다]\n{e}')
            self._text.config(state='disabled')


# ─── 진행률 다이얼로그 ────────────────────────────────────────────────────────
class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, title: str, theme: dict):
        super().__init__(parent)
        self.title(title)
        self.geometry('460x160')
        self.resizable(False, False)
        self.configure(bg=theme['main_bg'])
        self.transient(parent)
        self.grab_set()
        self._cancelled = False

        self._title_lbl = tk.Label(self, text=title, font=(UI_FONT, 11, 'bold'),
                                   bg=theme['main_bg'], fg=theme['toolbar_fg'])
        self._title_lbl.pack(pady=(14, 4))

        self._file_lbl = tk.Label(self, text='준비 중...', font=(UI_FONT, 9),
                                  bg=theme['main_bg'], fg=theme['status_fg'],
                                  wraplength=420, anchor='w')
        self._file_lbl.pack(fill='x', padx=20)

        self._pb = ttk.Progressbar(self, mode='determinate', length=420)
        self._pb.pack(padx=20, pady=8)

        self._pct_lbl = tk.Label(self, text='0 / 0', font=(UI_FONT, 9),
                                 bg=theme['main_bg'], fg=theme['status_fg'])
        self._pct_lbl.pack()

        tk.Button(self, text='취소', command=self._cancel,
                  bg='#E74C3C', fg='#FFFFFF', relief='flat',
                  font=(UI_FONT, 9), padx=16, cursor='hand2').pack(pady=(4, 10))

        self.protocol('WM_DELETE_WINDOW', self._cancel)

    def _cancel(self):
        self._cancelled = True

    def update_progress(self, current: int, total: int, filename: str):
        if self._cancelled:
            return
        pct = (current / total * 100) if total else 0
        self._pb['value'] = pct
        self._file_lbl.config(text=f'처리 중: {filename}')
        self._pct_lbl.config(text=f'{current} / {total}  ({pct:.0f}%)')
        self.update_idletasks()

    @property
    def cancelled(self):
        return self._cancelled


# ─── 일괄 이름바꾸기 ─────────────────────────────────────────────────────────
class BatchRenameDialog(tk.Toplevel):
    def __init__(self, parent, files: list, theme: dict, on_done):
        super().__init__(parent)
        self.title('일괄 이름바꾸기')
        self.geometry('680x520')
        self.configure(bg=theme['main_bg'])
        self.transient(parent)
        self.grab_set()
        self._files   = files
        self._theme   = theme
        self._on_done = on_done

        p = theme

        # 옵션 프레임
        opt = tk.LabelFrame(self, text=' 변환 규칙 ', font=(UI_FONT, 9),
                            bg=p['main_bg'], fg=p['toolbar_fg'],
                            padx=10, pady=8)
        opt.pack(fill='x', padx=12, pady=(10, 4))

        # 검색/치환
        row = tk.Frame(opt, bg=p['main_bg'])
        row.pack(fill='x', pady=2)
        tk.Label(row, text='검색:', width=8, anchor='e',
                 bg=p['main_bg'], fg=p['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left')
        self._find = tk.Entry(row, width=22, font=(UI_FONT, 9),
                              bg=p['entry_bg'], fg=p['entry_fg'], relief='solid', bd=1)
        self._find.pack(side='left', padx=4)
        tk.Label(row, text='→ 치환:', anchor='e',
                 bg=p['main_bg'], fg=p['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left')
        self._replace = tk.Entry(row, width=22, font=(UI_FONT, 9),
                                 bg=p['entry_bg'], fg=p['entry_fg'], relief='solid', bd=1)
        self._replace.pack(side='left', padx=4)

        # 접두사/접미사
        row2 = tk.Frame(opt, bg=p['main_bg'])
        row2.pack(fill='x', pady=2)
        tk.Label(row2, text='접두사:', width=8, anchor='e',
                 bg=p['main_bg'], fg=p['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left')
        self._prefix = tk.Entry(row2, width=22, font=(UI_FONT, 9),
                                bg=p['entry_bg'], fg=p['entry_fg'], relief='solid', bd=1)
        self._prefix.pack(side='left', padx=4)
        tk.Label(row2, text='접미사:', anchor='e',
                 bg=p['main_bg'], fg=p['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left')
        self._suffix = tk.Entry(row2, width=22, font=(UI_FONT, 9),
                                bg=p['entry_bg'], fg=p['entry_fg'], relief='solid', bd=1)
        self._suffix.pack(side='left', padx=4)

        # 번호 매기기
        row3 = tk.Frame(opt, bg=p['main_bg'])
        row3.pack(fill='x', pady=2)
        self._num_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row3, text='번호 자동추가', variable=self._num_var,
                       bg=p['main_bg'], fg=p['toolbar_fg'],
                       selectcolor=p['main_bg'], activebackground=p['main_bg'],
                       font=(UI_FONT, 9)).pack(side='left')
        tk.Label(row3, text='시작번호:', bg=p['main_bg'], fg=p['toolbar_fg'],
                 font=(UI_FONT, 9)).pack(side='left', padx=(20, 4))
        self._num_start = tk.Spinbox(row3, from_=1, to=9999, width=6,
                                     font=(UI_FONT, 9), bg=p['entry_bg'], fg=p['entry_fg'])
        self._num_start.pack(side='left')
        tk.Label(row3, text='자리수:', bg=p['main_bg'], fg=p['toolbar_fg'],
                 font=(UI_FONT, 9)).pack(side='left', padx=(12, 4))
        self._num_pad = tk.Spinbox(row3, from_=1, to=8, width=4,
                                   font=(UI_FONT, 9), bg=p['entry_bg'], fg=p['entry_fg'])
        self._num_pad.pack(side='left')
        self._num_pad.delete(0, 'end'); self._num_pad.insert(0, '2')

        # 대소문자
        row4 = tk.Frame(opt, bg=p['main_bg'])
        row4.pack(fill='x', pady=2)
        self._case = tk.StringVar(value='none')
        tk.Label(row4, text='대소문자:', width=8, anchor='e',
                 bg=p['main_bg'], fg=p['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left')
        for val, lbl in [('none','변경없음'),('upper','대문자'),('lower','소문자'),('title','단어앞대문자')]:
            tk.Radiobutton(row4, text=lbl, variable=self._case, value=val,
                           bg=p['main_bg'], fg=p['toolbar_fg'],
                           selectcolor=p['main_bg'], activebackground=p['main_bg'],
                           font=(UI_FONT, 9)).pack(side='left', padx=4)

        tk.Button(opt, text='미리보기 갱신', command=self._preview,
                  bg=p['accent'], fg=p['accent_fg'], relief='flat',
                  font=(UI_FONT, 9), padx=10, cursor='hand2').pack(side='right')

        # 미리보기 트리
        pf = tk.Frame(self, bg=p['panel_bg'], relief='sunken', bd=1)
        pf.pack(fill='both', expand=True, padx=12, pady=4)
        columns = ('before', 'after')
        self._tree = ttk.Treeview(pf, columns=columns, show='headings', height=10)
        self._tree.heading('before', text='변경 전')
        self._tree.heading('after',  text='변경 후')
        self._tree.column('before', width=290)
        self._tree.column('after',  width=290)
        sb = ttk.Scrollbar(pf, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self._tree.pack(fill='both', expand=True)

        # 버튼
        bf = tk.Frame(self, bg=p['main_bg'])
        bf.pack(fill='x', padx=12, pady=(4, 12))
        tk.Button(bf, text='✔ 적용', command=self._apply,
                  bg='#27AE60', fg='#FFFFFF', relief='flat',
                  font=(UI_FONT, 10, 'bold'), padx=18, pady=4, cursor='hand2').pack(side='left', padx=4)
        tk.Button(bf, text='✕ 취소', command=self.destroy,
                  bg='#7F8C8D', fg='#FFFFFF', relief='flat',
                  font=(UI_FONT, 10), padx=18, pady=4, cursor='hand2').pack(side='left', padx=4)

        self._preview()

    def _build_new_name(self, name: str, idx: int) -> str:
        base, ext = os.path.splitext(name)
        find    = self._find.get()
        replace = self._replace.get()
        prefix  = self._prefix.get()
        suffix  = self._suffix.get()
        case    = self._case.get()

        if find:
            base = base.replace(find, replace)
        if case == 'upper':
            base = base.upper()
        elif case == 'lower':
            base = base.lower()
        elif case == 'title':
            base = base.title()

        if self._num_var.get():
            pad   = int(self._num_pad.get() or 2)
            start = int(self._num_start.get() or 1)
            num_s = str(start + idx).zfill(pad)
            base  = base + '_' + num_s

        return prefix + base + suffix + ext

    def _preview(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        for idx, fp in enumerate(self._files):
            old = os.path.basename(fp)
            new = self._build_new_name(old, idx)
            tag = '' if old != new else 'same'
            self._tree.insert('', 'end', values=(old, new), tags=(tag,))
        self._tree.tag_configure('same', foreground='gray')

    def _apply(self):
        errors = []
        for idx, fp in enumerate(self._files):
            old = os.path.basename(fp)
            new = self._build_new_name(old, idx)
            if old == new:
                continue
            new_path = os.path.join(os.path.dirname(fp), new)
            try:
                os.rename(fp, new_path)
            except Exception as e:
                errors.append(f'{old}: {e}')
        if errors:
            messagebox.showerror('오류', '일부 파일 이름 변경 실패:\n' + '\n'.join(errors[:10]))
        else:
            messagebox.showinfo('완료', '일괄 이름 변경이 완료되었습니다.')
        self._on_done()
        self.destroy()


# ─── 북마크 사이드바 ─────────────────────────────────────────────────────────
class BookmarkPanel(tk.Frame):
    """즐겨찾기 + 최근 경로 사이드바"""

    # 기본 시스템 폴더 (첫 실행 시 자동 추가)
    _SYSTEM_FOLDERS = []

    def __init__(self, parent, theme: dict, on_navigate, recent_paths: list = None):
        super().__init__(parent)
        self._theme        = theme
        self._on_navigate  = on_navigate
        self._bookmarks: list = []
        self._recent: list    = recent_paths if recent_paths is not None else []
        self._mode            = 'bookmark'   # 'bookmark' | 'recent'
        self._load()
        self._init_system_folders()
        self._build()

    # ─ 시스템 기본 폴더 자동 추가 ──────────────────────────────────────────
    def _init_system_folders(self):
        """북마크가 비어있을 때 기본 시스템 폴더를 자동 추가"""
        if self._bookmarks:
            return
        home = Path.home()
        candidates = [
            home,
            home / 'Desktop',
            home / '바탕화면',
            home / 'Documents',
            home / '문서',
            home / 'Downloads',
            home / '다운로드',
            home / 'Pictures',
            home / '사진',
        ]
        for p in candidates:
            sp = str(p)
            if p.exists() and sp not in self._bookmarks:
                self._bookmarks.append(sp)
        if self._bookmarks:
            self._save()

    # ─ UI 빌드 ────────────────────────────────────────────────────────────
    def _build(self):
        p = self._theme
        self.configure(bg=p['bmark_bg'], relief='flat')

        # ── 탭 헤더 ─────────────────────────
        hdr = tk.Frame(self, bg=p['toolbar_bg'], pady=3)
        hdr.pack(fill='x')

        self._tab_bm_btn = tk.Button(
            hdr, text='⭐ 즐겨찾기',
            command=lambda: self._switch_mode('bookmark'),
            bg=p['accent'], fg=p['accent_fg'],
            relief='flat', font=(UI_FONT, 8, 'bold'),
            cursor='hand2', padx=4, pady=2)
        self._tab_bm_btn.pack(side='left', padx=(4, 1), pady=2)

        self._tab_rc_btn = tk.Button(
            hdr, text='🕐 최근경로',
            command=lambda: self._switch_mode('recent'),
            bg=p['btn_bg'], fg=p['btn_fg'],
            relief='flat', font=(UI_FONT, 8),
            cursor='hand2', padx=4, pady=2)
        self._tab_rc_btn.pack(side='left', padx=(1, 4), pady=2)

        # ── 즐겨찾기 도구 버튼 ───────────────
        self._bmark_tools = tk.Frame(self, bg=p['toolbar_bg'])
        self._bmark_tools.pack(fill='x')

        def small_btn(parent, text, cmd, tip=''):
            b = tk.Button(parent, text=text, command=cmd,
                          bg=p['btn_bg'], fg=p['btn_fg'],
                          relief='flat', font=(UI_FONT, 8),
                          cursor='hand2', padx=3, pady=1)
            b.pack(side='left', padx=2, pady=2)
            return b

        small_btn(self._bmark_tools, '+ 추가', self._add_current)
        small_btn(self._bmark_tools, '▲',      self._move_up)
        small_btn(self._bmark_tools, '▼',      self._move_down)
        small_btn(self._bmark_tools, '✕ 삭제', self._remove_selected)

        # ── 목록 ─────────────────────────────
        list_frame = tk.Frame(self, bg=p['bmark_bg'])
        list_frame.pack(fill='both', expand=True)

        sb = ttk.Scrollbar(list_frame)
        sb.pack(side='right', fill='y')
        self._lb = tk.Listbox(list_frame, yscrollcommand=sb.set,
                              bg=p['bmark_bg'], fg=p['bmark_fg'],
                              selectbackground=p['bmark_sel'],
                              selectforeground=p['bmark_fg'],
                              font=(UI_FONT, 9), relief='flat',
                              activestyle='none', cursor='hand2',
                              borderwidth=0, highlightthickness=0)
        sb.config(command=self._lb.yview)
        self._lb.pack(fill='both', expand=True)

        # 단일 클릭 이동
        self._lb.bind('<Button-1>',   self._on_click)
        self._lb.bind('<Button-3>',   self._context_menu)
        self._lb.bind('<Motion>',     self._on_lb_motion)
        self._lb.bind('<Leave>',      self._on_lb_leave)

        # 툴팁
        self._tip_win  = None
        self._tip_idx  = -1

        # 현재 경로 참조용
        self.current_path_ref = None

        self._refresh_lb()
        self._update_tab_style()

    # ─ 모드 전환 ──────────────────────────────────────────────────────────
    def _switch_mode(self, mode: str):
        self._mode = mode
        self._update_tab_style()
        self._refresh_lb()

    def _update_tab_style(self):
        p = self._theme
        is_bm = (self._mode == 'bookmark')
        self._tab_bm_btn.config(
            bg=p['accent'] if is_bm else p['btn_bg'],
            fg=p['accent_fg'] if is_bm else p['btn_fg'],
            font=(UI_FONT, 8, 'bold' if is_bm else 'normal'))
        self._tab_rc_btn.config(
            bg=p['accent'] if not is_bm else p['btn_bg'],
            fg=p['accent_fg'] if not is_bm else p['btn_fg'],
            font=(UI_FONT, 8, 'bold' if not is_bm else 'normal'))
        # 즐겨찾기 모드에서만 편집 도구 표시
        if is_bm:
            self._bmark_tools.pack(fill='x', after=self._tab_bm_btn.master)
        else:
            self._bmark_tools.pack_forget()

    # ─ 목록 갱신 ──────────────────────────────────────────────────────────
    def _refresh_lb(self):
        self._lb.delete(0, 'end')
        items = self._bookmarks if self._mode == 'bookmark' else self._recent
        for path in items:
            icon = '📂' if os.path.isdir(path) else ('🕐' if self._mode == 'recent' else '📄')
            label = os.path.basename(path) or path
            self._lb.insert('end', f'{icon}  {label}')

    def _current_list(self) -> list:
        return self._bookmarks if self._mode == 'bookmark' else self._recent

    # ─ 단일클릭 이동 ──────────────────────────────────────────────────────
    def _on_click(self, event):
        idx = self._lb.nearest(event.y)
        if idx < 0:
            return
        self._lb.selection_clear(0, 'end')
        self._lb.selection_set(idx)
        items = self._current_list()
        if idx < len(items) and self._on_navigate:
            self._on_navigate(items[idx])

    # ─ 툴팁 ───────────────────────────────────────────────────────────────
    def _on_lb_motion(self, event):
        idx = self._lb.nearest(event.y)
        if idx == self._tip_idx:
            return
        self._hide_tip()
        self._tip_idx = idx
        items = self._current_list()
        if 0 <= idx < len(items):
            path = items[idx]
            t = tk.Toplevel()
            t.wm_overrideredirect(True)
            t.wm_geometry(f'+{event.x_root+14}+{event.y_root+12}')
            tk.Label(t, text=path, bg='#FFFFCC', fg='#333333',
                     relief='solid', bd=1, padx=5, pady=2,
                     font=(UI_FONT, 8)).pack()
            self._tip_win = t

    def _on_lb_leave(self, event):
        self._hide_tip()

    def _hide_tip(self):
        if self._tip_win:
            self._tip_win.destroy()
            self._tip_win = None
        self._tip_idx = -1

    # ─ 즐겨찾기 편집 ─────────────────────────────────────────────────────
    def _add_current(self):
        if self.current_path_ref is None:
            return
        path = self.current_path_ref()
        if path and path not in self._bookmarks:
            self._bookmarks.append(path)
            self._save()
            self._refresh_lb()

    def _remove_selected(self):
        sel = self._lb.curselection()
        if not sel:
            return
        idx = sel[0]
        if self._mode == 'bookmark' and 0 <= idx < len(self._bookmarks):
            del self._bookmarks[idx]
            self._save()
            self._refresh_lb()
        elif self._mode == 'recent' and 0 <= idx < len(self._recent):
            del self._recent[idx]
            self._refresh_lb()

    def _move_up(self):
        if self._mode != 'bookmark':
            return
        sel = self._lb.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self._bookmarks[idx-1], self._bookmarks[idx] = \
            self._bookmarks[idx], self._bookmarks[idx-1]
        self._save()
        self._refresh_lb()
        self._lb.selection_set(idx - 1)

    def _move_down(self):
        if self._mode != 'bookmark':
            return
        sel = self._lb.curselection()
        if not sel or sel[0] >= len(self._bookmarks) - 1:
            return
        idx = sel[0]
        self._bookmarks[idx], self._bookmarks[idx+1] = \
            self._bookmarks[idx+1], self._bookmarks[idx]
        self._save()
        self._refresh_lb()
        self._lb.selection_set(idx + 1)

    # ─ 컨텍스트 메뉴 ──────────────────────────────────────────────────────
    def _context_menu(self, event):
        idx = self._lb.nearest(event.y)
        items = self._current_list()
        if idx < 0 or idx >= len(items):
            return
        self._lb.selection_clear(0, 'end')
        self._lb.selection_set(idx)
        p = self._theme
        menu = tk.Menu(self, tearoff=0, bg=p['panel_bg'], fg=p['tree_fg'],
                       activebackground=p['accent'], activeforeground=p['accent_fg'])
        menu.add_command(label='이동', command=lambda: self._on_click(event))
        if self._mode == 'bookmark':
            menu.add_separator()
            menu.add_command(label='위로 이동', command=self._move_up)
            menu.add_command(label='아래로 이동', command=self._move_down)
            menu.add_separator()
            menu.add_command(label='삭제', command=self._remove_selected)
        else:
            menu.add_separator()
            menu.add_command(label='즐겨찾기에 추가', command=lambda: self._add_from_recent(idx))
            menu.add_command(label='목록에서 제거', command=self._remove_selected)
        menu.post(event.x_root, event.y_root)

    def _add_from_recent(self, idx: int):
        if idx < len(self._recent):
            path = self._recent[idx]
            if path not in self._bookmarks:
                self._bookmarks.append(path)
                self._save()

    # ─ 최근경로 갱신 ──────────────────────────────────────────────────────
    def add_recent(self, path: str):
        if path in self._recent:
            self._recent.remove(path)
        self._recent.insert(0, path)
        if len(self._recent) > RECENT_MAX:
            self._recent = self._recent[:RECENT_MAX]
        if self._mode == 'recent':
            self._refresh_lb()

    # ─ 로드/저장 ──────────────────────────────────────────────────────────
    def _load(self):
        try:
            if os.path.exists(BOOKMARKS_FILE):
                with open(BOOKMARKS_FILE, 'r', encoding='utf-8') as f:
                    self._bookmarks = json.load(f)
        except Exception:
            self._bookmarks = []

    def _save(self):
        try:
            with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._bookmarks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ─ 테마 적용 ──────────────────────────────────────────────────────────
    def apply_theme(self, theme: dict):
        self._theme = theme
        p = theme
        self.configure(bg=p['bmark_bg'])
        self._lb.configure(bg=p['bmark_bg'], fg=p['bmark_fg'],
                           selectbackground=p['bmark_sel'], selectforeground=p['bmark_fg'])
        self._update_tab_style()
        for child in self.winfo_children():
            try:
                child.configure(bg=p['bmark_bg'])
            except Exception:
                pass


# ─── 브레드크럼 바 ───────────────────────────────────────────────────────────
class BreadcrumbBar(tk.Frame):
    def __init__(self, parent, theme: dict, on_navigate):
        super().__init__(parent)
        self._theme       = theme
        self._on_navigate = on_navigate
        self._path        = ''
        self.configure(bg=theme['crumb_bg'])

    def set_path(self, path: str):
        self._path = path
        p = self._theme
        for w in self.winfo_children():
            w.destroy()
        parts = Path(path).parts
        for i, part in enumerate(parts):
            full = str(Path(*parts[:i+1]))
            btn = tk.Button(self, text=part or '/',
                            command=lambda fp=full: self._on_navigate(fp),
                            bg=p['crumb_bg'], fg=p['crumb_fg'],
                            relief='flat', font=(UI_FONT, 9),
                            activebackground=p['accent'],
                            activeforeground=p['accent_fg'],
                            cursor='hand2', padx=4, pady=2,
                            borderwidth=0)
            btn.pack(side='left')
            if i < len(parts) - 1:
                tk.Label(self, text='›', bg=p['crumb_bg'],
                         fg=p['crumb_sep'], font=(UI_FONT, 10)).pack(side='left')

    def apply_theme(self, theme: dict):
        self._theme = theme
        self.configure(bg=theme['crumb_bg'])
        self.set_path(self._path)


# ─── 파일 패널 ───────────────────────────────────────────────────────────────
class FilePanel(tk.Frame):
    """단일 파일 패널 (탭 포함)"""

    def __init__(self, parent, side: str, app, theme: dict):
        super().__init__(parent)
        self._side    = side
        self._app     = app
        self._theme   = theme

        # 탭 데이터: list of {'path': str, 'history': [str], 'hist_idx': int}
        self._tabs: list = []
        self._cur_tab = 0

        home = str(Path.home())
        self._tabs.append({'path': home, 'history': [home], 'hist_idx': 0})

        # 정렬 상태
        self._sort_col  = 'name'
        self._sort_asc  = True
        # 필터
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add('write', lambda *_: self._apply_filter())
        # 드래그 앤 드롭 상태
        self._drag_start  = None   # (x_root, y_root)
        self._drag_active = False

        self._build()

    # ── 빌드 ────────────────────────────────────
    def _build(self):
        p = self._theme

        # 탭바
        self._tabbar = tk.Frame(self, bg=p['toolbar_bg'], height=28)
        self._tabbar.pack(fill='x')
        self._rebuild_tabs()

        # 경로 + 브레드크럼
        crumb_frame = tk.Frame(self, bg=p['crumb_bg'])
        crumb_frame.pack(fill='x')
        self.crumb = BreadcrumbBar(crumb_frame, p, self._navigate_breadcrumb)
        self.crumb.pack(side='left', fill='x', expand=True)

        if platform.system() == 'Windows':
            tk.Button(crumb_frame, text='💾', command=self._select_drive,
                      bg=p['crumb_bg'], fg=p['crumb_fg'], relief='flat',
                      font=(UI_FONT, 11), cursor='hand2',
                      activebackground=p['accent'], activeforeground=p['accent_fg']
                      ).pack(side='right', padx=4)

        # 경로 입력
        path_row = tk.Frame(self, bg=p['toolbar_bg'], pady=3)
        path_row.pack(fill='x')
        self._path_var = tk.StringVar(value=self._tabs[0]['path'])
        self._path_entry = tk.Entry(path_row, textvariable=self._path_var,
                                    font=(UI_FONT, 9), bg=p['entry_bg'],
                                    fg=p['entry_fg'], relief='solid', bd=1,
                                    insertbackground=p['entry_fg'])
        self._path_entry.pack(fill='x', padx=6, pady=2)
        self._path_entry.bind('<Return>', lambda _: self._go_to_entry())

        # 필터바
        filter_row = tk.Frame(self, bg=p['toolbar_bg'], pady=2)
        filter_row.pack(fill='x')
        tk.Label(filter_row, text='🔍', bg=p['toolbar_bg'],
                 fg=p['toolbar_fg'], font=(UI_FONT, 10)).pack(side='left', padx=(6, 2))
        self._filter_entry = tk.Entry(filter_row, textvariable=self._filter_var,
                                      font=(UI_FONT, 9), bg=p['filter_bg'],
                                      fg=p['filter_fg'], relief='solid', bd=1,
                                      insertbackground=p['filter_fg'])
        self._filter_entry.pack(side='left', fill='x', expand=True, padx=4)
        self._filter_entry.bind('<Escape>', lambda _: (self._filter_var.set(''), None))
        # × 클리어 버튼
        tk.Button(filter_row, text='✕', command=lambda: self._filter_var.set(''),
                  bg=p['toolbar_bg'], fg=p['toolbar_fg'], relief='flat',
                  font=(UI_FONT, 8), cursor='hand2', padx=2).pack(side='left')
        # 결과 수 레이블
        self._filter_count_lbl = tk.Label(filter_row, text='', bg=p['toolbar_bg'],
                                          fg=p['accent'], font=(UI_FONT, 8, 'bold'),
                                          width=8, anchor='e')
        self._filter_count_lbl.pack(side='left', padx=(0, 6))

        # 트리뷰
        tree_frame = tk.Frame(self, bg=p['panel_bg'])
        tree_frame.pack(fill='both', expand=True)

        xsb = ttk.Scrollbar(tree_frame, orient='horizontal')
        ysb = ttk.Scrollbar(tree_frame, orient='vertical')
        columns = ('size', 'date', 'type')
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                 show='tree headings',
                                 yscrollcommand=ysb.set,
                                 xscrollcommand=xsb.set,
                                 selectmode='extended')
        ysb.config(command=self.tree.yview)
        xsb.config(command=self.tree.xview)

        self.tree.heading('#0',    text='이름 ↕',   command=lambda: self._sort_by('name'))
        self.tree.heading('size',  text='크기 ↕',   command=lambda: self._sort_by('size'))
        self.tree.heading('date',  text='수정 날짜 ↕', command=lambda: self._sort_by('date'))
        self.tree.heading('type',  text='종류 ↕',   command=lambda: self._sort_by('type'))
        self.tree.column('#0',    width=300, minwidth=120)
        self.tree.column('size',  width=90,  minwidth=70, anchor='e')
        self.tree.column('date',  width=140, minwidth=110)
        self.tree.column('type',  width=100, minwidth=70)

        xsb.pack(side='bottom', fill='x')
        ysb.pack(side='right',  fill='y')
        self.tree.pack(fill='both', expand=True)

        self._configure_tree_tags()

        # 이벤트
        self.tree.bind('<FocusIn>',           lambda _: self._app.set_active(self._side))
        self.tree.bind('<Double-Button-1>',    lambda _: self._on_activate())
        self.tree.bind('<Return>',             lambda _: self._on_activate())
        self.tree.bind('<Control-a>',          lambda _: self._select_all())
        self.tree.bind('<Delete>',             lambda _: self._app.delete_files())
        self.tree.bind('<F2>',                 lambda _: self._app.rename_file())
        self.tree.bind('<<TreeviewSelect>>',   lambda _: self._on_select_change())
        self.tree.bind('<space>',              lambda _: self._toggle_focus_item())

        # 드래그 앤 드롭
        self.tree.bind('<ButtonPress-1>',   self._on_drag_start)
        self.tree.bind('<B1-Motion>',       self._on_drag_motion)
        self.tree.bind('<ButtonRelease-1>', self._on_drag_release)

        # 우클릭 메뉴
        self._ctx_menu = self._build_context_menu()
        self.tree.bind('<Button-3>', self._show_ctx_menu)

        # 상태바
        self._status = tk.Label(self, text='', anchor='w', padx=6,
                                bg=p['status_bg'], fg=p['status_fg'],
                                font=(UI_FONT, 8), relief='sunken', bd=1)
        self._status.pack(fill='x', side='bottom')

        self.crumb.set_path(self.current_path)
        self.refresh()

    def _configure_tree_tags(self):
        p = self._theme
        theme_name = getattr(self._app, '_theme_name', '라이트')
        tc = TYPE_COLORS.get(theme_name, TYPE_COLORS['라이트'])

        # 기본 태그
        self.tree.tag_configure('dir',    foreground=p['tree_fg'], background=p['tree_bg'])
        self.tree.tag_configure('file',   foreground=p['tree_fg'], background=p['tree_bg'])
        self.tree.tag_configure('parent', foreground=p['tree_fg'], background=p['tree_bg'])
        self.tree.tag_configure('altrow', background=p['tree_alt'])
        self.tree.tag_configure('dir_alt',  foreground=p['tree_fg'], background=p['tree_alt'])
        self.tree.tag_configure('file_alt', foreground=p['tree_fg'], background=p['tree_alt'])

        # 종류별 색상 태그
        for cat, (bg_n, bg_a) in tc.items():
            self.tree.tag_configure(cat,          foreground=p['tree_fg'], background=bg_n)
            self.tree.tag_configure(f'{cat}_alt', foreground=p['tree_fg'], background=bg_a)


    # ── 드래그 앤 드롭 ─────────────────────────
    def _on_drag_start(self, event):
        # 드래그 시작 위치 기록 (아직 드래그 판정은 보류)
        self._drag_start  = (event.x_root, event.y_root)
        self._drag_active = False

    def _on_drag_motion(self, event):
        if self._drag_start is None:
            return
        dx = abs(event.x_root - self._drag_start[0])
        dy = abs(event.y_root - self._drag_start[1])
        if not self._drag_active and (dx > 6 or dy > 6):
            paths = self.get_selected_paths()
            if paths:
                self._drag_active = True
                self._app.drag_manager.start(self, paths)
        if self._drag_active:
            self._app.drag_manager.motion(event)

    def _on_drag_release(self, event):
        if self._drag_active:
            self._app.drag_manager.drop(event)
        self._drag_start  = None
        self._drag_active = False

    # ── 탭 관리 ─────────────────────────────────
    def _rebuild_tabs(self):
        p = self._theme
        for w in self._tabbar.winfo_children():
            w.destroy()
        for i, tab in enumerate(self._tabs):
            name = os.path.basename(tab['path']) or tab['path']
            active = (i == self._cur_tab)
            bg = p['tab_active'] if active else p['tab_inactive']
            frm = tk.Frame(self._tabbar, bg=bg, relief='raised', bd=1)
            frm.pack(side='left', padx=1, pady=2)
            lbl = tk.Label(frm, text=f' {name[:14]} ', bg=bg, fg=p['tab_fg'],
                           font=(UI_FONT, 8, 'bold' if active else 'normal'),
                           cursor='hand2', padx=2)
            lbl.pack(side='left')
            lbl.bind('<Button-1>', lambda _, idx=i: self._switch_tab(idx))
            if len(self._tabs) > 1:
                x_btn = tk.Label(frm, text='×', bg=bg, fg=p['tab_fg'],
                                 font=(UI_FONT, 8), cursor='hand2', padx=1)
                x_btn.pack(side='left')
                x_btn.bind('<Button-1>', lambda _, idx=i: self.close_tab(idx))

        # 탭 추가 버튼
        tk.Button(self._tabbar, text='+', command=self.new_tab,
                  bg=p['toolbar_bg'], fg=p['toolbar_fg'],
                  relief='flat', font=(UI_FONT, 9), width=2,
                  cursor='hand2', activebackground=p['accent'],
                  activeforeground=p['accent_fg']).pack(side='left', padx=2)

    def new_tab(self, path: str = None):
        path = path or self.current_path
        self._tabs.append({'path': path, 'history': [path], 'hist_idx': 0})
        self._cur_tab = len(self._tabs) - 1
        self._sync_path()
        self._rebuild_tabs()
        self.refresh()

    def close_tab(self, idx: int):
        if len(self._tabs) <= 1:
            return
        del self._tabs[idx]
        self._cur_tab = min(self._cur_tab, len(self._tabs) - 1)
        self._sync_path()
        self._rebuild_tabs()
        self.refresh()

    def _switch_tab(self, idx: int):
        self._cur_tab = idx
        self._sync_path()
        self._rebuild_tabs()
        self.refresh()

    def _sync_path(self):
        self._path_var.set(self.current_path)

    @property
    def current_path(self) -> str:
        return self._tabs[self._cur_tab]['path']

    @current_path.setter
    def current_path(self, path: str):
        self._tabs[self._cur_tab]['path'] = path
        self._path_var.set(path)

    # ── 탐색 ────────────────────────────────────
    def navigate(self, path: str, add_history: bool = True):
        if not os.path.isdir(path):
            return
        tab = self._tabs[self._cur_tab]
        if add_history:
            tab['history'] = tab['history'][:tab['hist_idx'] + 1]
            tab['history'].append(path)
            tab['hist_idx'] = len(tab['history']) - 1
        self.current_path = path
        self._filter_var.set('')
        self.crumb.set_path(path)
        self._rebuild_tabs()
        self.refresh()
        # 최근 경로 기록
        self._app.add_recent_path(path)

    def navigate_back(self):
        tab = self._tabs[self._cur_tab]
        if tab['hist_idx'] > 0:
            tab['hist_idx'] -= 1
            self.navigate(tab['history'][tab['hist_idx']], add_history=False)

    def navigate_forward(self):
        tab = self._tabs[self._cur_tab]
        if tab['hist_idx'] < len(tab['history']) - 1:
            tab['hist_idx'] += 1
            self.navigate(tab['history'][tab['hist_idx']], add_history=False)

    def navigate_up(self):
        cur  = self.current_path
        parent = os.path.dirname(cur)
        if parent != cur:
            self.navigate(parent)

    def _go_to_entry(self):
        path = self._path_var.get().strip()
        if os.path.isdir(path):
            self.navigate(path)
        else:
            messagebox.showerror('오류', '유효하지 않은 경로입니다.')

    def _navigate_breadcrumb(self, path: str):
        if os.path.isdir(path):
            self.navigate(path)

    def _select_drive(self):
        self._app.select_drive(self._side)

    # ── 새로고침 ─────────────────────────────────
    def refresh(self):
        path = self.current_path
        flt  = self._filter_var.get().strip()

        # 현재 선택 기억
        prev_sel = {self._strip(self.tree.item(i)['text'])
                    for i in self.tree.selection()}

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(path):
            self._status.config(text='경로를 찾을 수 없습니다.')
            return

        rows = []
        try:
            for name in os.listdir(path):
                if not self._app.view_hidden.get() and name.startswith('.'):
                    continue
                full = os.path.join(path, name)
                try:
                    st     = os.stat(full)
                    is_dir = os.path.isdir(full)
                    size_b = st.st_size if not is_dir else -1
                    mtime  = st.st_mtime
                    ftype  = '폴더' if is_dir else get_file_type(name)
                    rows.append((name, is_dir, size_b, mtime, ftype))
                except Exception:
                    continue
        except PermissionError:
            self._status.config(text='액세스 거부됨')
            return

        # 정렬
        key_map = {
            'name': lambda r: (not r[1], r[0].lower()),
            'size': lambda r: (not r[1], r[2]),
            'date': lambda r: (not r[1], r[3]),
            'type': lambda r: (not r[1], r[4].lower()),
        }
        rows.sort(key=key_map.get(self._sort_col, key_map['name']),
                  reverse=not self._sort_asc)

        # ── 필터 함수 결정 ───────────────────
        def _matches(name: str) -> bool:
            if not flt:
                return True
            nl = name.lower()
            fl = flt.lower()
            # 확장자 필터: ".py" 형식
            if fl.startswith('.') and ' ' not in fl and '*' not in fl:
                return nl.endswith(fl)
            # 와일드카드 패턴: "*" 포함
            if '*' in fl or '?' in fl:
                return fnmatch.fnmatch(nl, fl)
            # 기본 부분문자열 검색
            return fl in nl

        # 상위 폴더
        if os.path.dirname(path) != path:
            self.tree.insert('', 'end', text='📁  ..', values=('', '', '상위 폴더'),
                             tags=('parent',))

        restore      = []
        max_name_len = 4   # 컬럼 자동조절용
        visible_cnt  = 0

        for idx, (name, is_dir, size_b, mtime, ftype) in enumerate(rows):
            if not _matches(name):
                continue
            visible_cnt += 1
            icon = '📁' if is_dir else get_file_icon(name)
            text = f'{icon}  {name}'
            size_s = '' if is_dir else format_size(size_b)
            date_s = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            alt    = idx % 2 == 1
            if is_dir:
                tag = 'dir_alt' if alt else 'dir'
            else:
                tag = get_type_tag(ftype, alt)
            iid = self.tree.insert('', 'end', text=text,
                                   values=(size_s, date_s, ftype),
                                   tags=(tag,))
            if name in prev_sel:
                restore.append(iid)
            # 이름 길이 추적 (자동조절용)
            if len(name) > max_name_len:
                max_name_len = len(name)

        if restore:
            self.tree.selection_set(restore)

        # 필터 결과 수 표시
        if flt:
            self._filter_count_lbl.config(text=f'{visible_cnt}개')
        else:
            self._filter_count_lbl.config(text='')

        self._update_status(len(rows))

        # ── 컬럼 너비 자동조절 ───────────────
        # 이름 컬럼: 파일명 최대 길이 기반 (폰트 픽셀 근사치 7px/char)
        name_w = max(180, min(max_name_len * 7 + 40, 480))
        self.tree.column('#0', width=name_w)

    def _apply_filter(self):
        self.refresh()

    # ── 선택 ────────────────────────────────────
    def _select_all(self):
        items = [i for i in self.tree.get_children()
                 if self._strip(self.tree.item(i)['text']) != '..']
        self.tree.selection_set(items)

    def _toggle_focus_item(self):
        focused = self.tree.focus()
        if focused:
            if focused in self.tree.selection():
                self.tree.selection_remove(focused)
            else:
                self.tree.selection_add(focused)

    def get_selected_paths(self) -> list:
        result = []
        for iid in self.tree.selection():
            name = self._strip(self.tree.item(iid)['text'])
            if name and name != '..':
                result.append(os.path.join(self.current_path, name))
        return result

    def _strip(self, text: str) -> str:
        # "icon  name" → "name"
        if '  ' in text:
            return text.split('  ', 1)[1].strip()
        return text.strip()

    # ── 활성화(더블클릭/Enter) ──────────────────
    def _on_activate(self):
        sel = self.tree.selection()
        if not sel:
            return
        text  = self.tree.item(sel[0])['text']
        name  = self._strip(text)
        path  = os.path.join(self.current_path, name)
        if name == '..':
            self.navigate_up()
        elif os.path.isdir(path):
            self.navigate(path)
        else:
            self._app.open_file(path)

    # ── 정렬 ────────────────────────────────────
    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        # 헤더 화살표 갱신
        labels = {'name': '이름', 'size': '크기', 'date': '수정 날짜', 'type': '종류'}
        col_keys = {'name': '#0', 'size': 'size', 'date': 'date', 'type': 'type'}
        for c, lbl in labels.items():
            arr = (' ↑' if self._sort_asc else ' ↓') if c == col else ' ↕'
            self.tree.heading(col_keys[c], text=lbl + arr)
        self.refresh()

    # ── 상태 ────────────────────────────────────
    def _on_select_change(self):
        self._update_status()
        self._app.set_active(self._side)

    def _update_status(self, total: int = None):
        p = self.current_path
        if total is None:
            total = len([i for i in self.tree.get_children()
                         if self._strip(self.tree.item(i)['text']) != '..'])
        sel   = self.tree.selection()
        names = [self._strip(self.tree.item(i)['text']) for i in sel
                 if self._strip(self.tree.item(i)['text']) != '..']
        if names:
            sel_size = 0
            for n in names:
                fp = os.path.join(p, n)
                if os.path.isfile(fp):
                    try:
                        sel_size += os.path.getsize(fp)
                    except Exception:
                        pass
            size_str = f'  |  선택 {format_size(sel_size)}' if sel_size > 0 else ''
            text = f'{len(names)}개 선택{size_str}  /  전체 {total}개'
        else:
            total_kb, used_kb, free_kb = get_disk_usage(p)
            if total_kb:
                disk_str = f'  |  디스크 여유: {format_size(free_kb)}'
            else:
                disk_str = ''
            text = f'전체 {total}개 항목{disk_str}'
        self._status.config(text=text)

    # ── 컨텍스트 메뉴 ────────────────────────────
    def _build_context_menu(self):
        p = self._theme
        menu = tk.Menu(self, tearoff=0, bg=p['panel_bg'], fg=p['tree_fg'],
                       activebackground=p['accent'], activeforeground=p['accent_fg'],
                       font=(UI_FONT, 9))
        menu.add_command(label='열기',              command=self._on_activate)
        menu.add_command(label='내장 뷰어로 보기',  command=lambda: self._app.view_file_internal())
        menu.add_separator()
        menu.add_command(label='복사 (F5)',          command=self._app.copy_files)
        menu.add_command(label='이동 (F6)',          command=self._app.move_files)
        menu.add_command(label='삭제 (F8/Del)',      command=self._app.delete_files)
        menu.add_separator()
        menu.add_command(label='이름 바꾸기 (F2)',   command=self._app.rename_file)
        menu.add_command(label='일괄 이름바꾸기',    command=self._app.batch_rename)
        menu.add_separator()
        menu.add_command(label='새 탭으로 열기',     command=lambda: self._open_in_new_tab())
        menu.add_command(label='즐겨찾기 추가',      command=lambda: self._app.bookmark_panel.current_path_ref and None)
        menu.add_separator()
        menu.add_command(label='경로 복사',          command=self._app.copy_path)
        menu.add_command(label='탐색기에서 열기',    command=self._app.open_in_explorer)
        menu.add_separator()
        menu.add_command(label='속성',              command=self._app.show_properties)
        return menu

    def _show_ctx_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._app.set_active(self._side)
        try:
            self._ctx_menu.post(event.x_root, event.y_root)
        finally:
            self._ctx_menu.grab_release()

    def _open_in_new_tab(self):
        sel = self.get_selected_paths()
        if sel and os.path.isdir(sel[0]):
            self.new_tab(sel[0])

    # ── 드라이브 선택 (Windows) ──────────────────
    def _select_drive(self):
        self._app.select_drive(self._side)

    # ── 테마 적용 ────────────────────────────────
    def apply_theme(self, theme: dict):
        self._theme = theme
        p = theme
        self.configure(bg=p['panel_bg'])
        self._tabbar.configure(bg=p['toolbar_bg'])
        self._status.configure(bg=p['status_bg'], fg=p['status_fg'])
        self._configure_tree_tags()
        self.crumb.apply_theme(theme)
        self._rebuild_tabs()
        self.refresh()


# ─── 드래그 앤 드롭 매니저 ───────────────────────────────────────────────────
class DragDropManager:
    """좌↔우 패널간 드래그 앤 드롭을 관리"""

    def __init__(self, app):
        self._app      = app
        self._data     = None   # {'panel': FilePanel, 'paths': [str]}
        self._ind      = None   # 인디케이터 Toplevel

    def start(self, panel, paths: list):
        self._data = {'panel': panel, 'paths': paths}

    def motion(self, event):
        if self._data is None:
            return
        if self._ind is None:
            self._ind = tk.Toplevel()
            self._ind.wm_overrideredirect(True)
            try:
                self._ind.attributes('-alpha', 0.80)
            except Exception:
                pass
            n = len(self._data['paths'])
            label = f'📋 {n}개 항목  (Ctrl=복사 / 기본=이동)'
            tk.Label(self._ind, text=label,
                     bg='#4A90D9', fg='white',
                     font=(UI_FONT, 9, 'bold'),
                     padx=10, pady=5).pack()
        self._ind.geometry(f'+{event.x_root + 12}+{event.y_root + 12}')

    def drop(self, event):
        self._hide()
        if self._data is None:
            return
        src_panel = self._data['panel']
        src_paths = self._data['paths']
        self._data = None

        app = self._app
        target = None
        for panel in (app.left_panel, app.right_panel):
            if panel is src_panel:
                continue
            px = panel.winfo_rootx()
            py = panel.winfo_rooty()
            if px <= event.x_root <= px + panel.winfo_width() and \
               py <= event.y_root <= py + panel.winfo_height():
                target = panel
                break

        if target is None:
            return

        dest = target.current_path
        ctrl = bool(event.state & 0x4)
        op   = 'copy' if ctrl else 'move'
        app._do_dnd_op(src_paths, dest, op, src_panel)

    def cancel(self):
        self._hide()
        self._data = None

    def _hide(self):
        if self._ind:
            self._ind.destroy()
            self._ind = None


# ─── 메인 앱 ─────────────────────────────────────────────────────────────────
class SimpleCommander:
    def __init__(self, root: tk.Tk):
        self.root     = root
        self.root.title('Simple Commander v2.1')

        self._settings = self._load_settings()
        theme_name = self._settings.get('theme', '라이트')
        self._theme_name = theme_name
        self.theme = THEMES[theme_name]

        # 최근 경로 히스토리
        self._recent_paths: list = self._settings.get('recent_paths', [])

        # 창 크기 복원
        w = self._settings.get('width',  1400)
        h = self._settings.get('height', 820)
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        root.geometry(f'{w}x{h}+{x}+{y}')
        root.minsize(900, 600)
        root.configure(bg=self.theme['main_bg'])

        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self._apply_ttk_style()

        self.view_hidden  = tk.BooleanVar(value=self._settings.get('hidden', False))
        self._active_side = 'left'
        self.drag_manager = DragDropManager(self)

        self._build_ui()
        self._setup_shortcuts()
        self.root.bind('<Configure>', self._on_resize)
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    # ── 설정 저장/로드 ───────────────────────────
    def _load_settings(self) -> dict:
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_settings(self):
        try:
            self._settings.update({
                'theme':        self._theme_name,
                'width':        self.root.winfo_width(),
                'height':       self.root.winfo_height(),
                'hidden':       self.view_hidden.get(),
                'sash':         self._sash_pos(),
                'recent_paths': self._recent_paths,
            })
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _sash_pos(self):
        try:
            return self._main_paned.sash_coord(0)[0]
        except Exception:
            return None

    def _on_resize(self, event):
        if event.widget is self.root:
            self._settings['width']  = self.root.winfo_width()
            self._settings['height'] = self.root.winfo_height()

    def _on_close(self):
        self._save_settings()
        self.root.destroy()

    # ── TTK 스타일 ──────────────────────────────
    def _apply_ttk_style(self):
        p = self.theme
        self.style.configure('Treeview',
            background=p['tree_bg'], foreground=p['tree_fg'],
            fieldbackground=p['tree_bg'], rowheight=26,
            font=(UI_FONT, 9))
        self.style.configure('Treeview.Heading',
            background=p['tree_head_bg'], foreground=p['tree_head_fg'],
            relief='flat', font=(UI_FONT, 9, 'bold'))
        self.style.map('Treeview',
            background=[('selected', p['tree_sel_bg'])],
            foreground=[('selected', p['tree_sel_fg'])])
        self.style.configure('Vertical.TScrollbar',
            background=p['panel_bg'], troughcolor=p['main_bg'],
            arrowcolor=p['toolbar_fg'])
        self.style.configure('Horizontal.TScrollbar',
            background=p['panel_bg'], troughcolor=p['main_bg'],
            arrowcolor=p['toolbar_fg'])
        self.style.configure('TCombobox',
            fieldbackground=p['entry_bg'], background=p['entry_bg'],
            foreground=p['entry_fg'])

    # ── UI 빌드 ─────────────────────────────────
    def _build_ui(self):
        p = self.theme

        # 메뉴바
        self._build_menu()

        # 툴바
        self._build_toolbar()

        # 좌우 분할 영역 (북마크 | 패널L | 패널R)
        outer = tk.Frame(self.root, bg=p['main_bg'])
        outer.pack(fill='both', expand=True)

        # 북마크 사이드바
        self.bookmark_panel = BookmarkPanel(
            outer, p,
            on_navigate=lambda path: self._active_panel().navigate(path),
            recent_paths=self._recent_paths)
        self.bookmark_panel.pack(side='left', fill='y')
        self.bookmark_panel.configure(width=160)
        self.bookmark_panel.pack_propagate(False)

        # 메인 패널 분할기
        self._main_paned = tk.PanedWindow(outer, orient='horizontal',
                                          bg=p['border'], sashwidth=5,
                                          sashrelief='flat', handlesize=10)
        self._main_paned.pack(fill='both', expand=True)

        self.left_panel  = FilePanel(self._main_paned, 'left',  self, p)
        self.right_panel = FilePanel(self._main_paned, 'right', self, p)
        self._main_paned.add(self.left_panel,  minsize=200, stretch='always')
        self._main_paned.add(self.right_panel, minsize=200, stretch='always')

        # 북마크 현재 경로 참조
        self.bookmark_panel.current_path_ref = lambda: self._active_panel().current_path

        # 하단 기능 버튼
        self._build_function_buttons()

        # 상태바
        self._build_statusbar()

        # sash 위치 복원 (없으면 50/50 기본값)
        sash = self._settings.get('sash')
        if sash:
            self.root.after(100, lambda: self._main_paned.sash_place(0, sash, 0))
        else:
            self.root.after(100, self._set_default_sash)

    def _set_default_sash(self):
        """좌우 패널을 정확히 반반(50:50)으로 초기화"""
        total = self._main_paned.winfo_width()
        if total > 1:
            self._main_paned.sash_place(0, total // 2, 0)

    def _build_menu(self):
        p = self.theme
        mb = tk.Menu(self.root, bg=p['panel_bg'], fg=p['tree_fg'],
                     activebackground=p['accent'], activeforeground=p['accent_fg'],
                     font=(UI_FONT, 9))
        self.root.config(menu=mb)

        def add_menu(label):
            m = tk.Menu(mb, tearoff=0, bg=p['panel_bg'], fg=p['tree_fg'],
                        activebackground=p['accent'], activeforeground=p['accent_fg'],
                        font=(UI_FONT, 9))
            mb.add_cascade(label=label, menu=m)
            return m

        fm = add_menu('파일')
        fm.add_command(label='새 폴더  (F7)',        command=self.new_folder)
        fm.add_command(label='새 파일',              command=self.new_file)
        fm.add_separator()
        fm.add_command(label='속성',                 command=self.show_properties)
        fm.add_separator()
        fm.add_command(label='종료',                 command=self._on_close)

        em = add_menu('편집')
        em.add_command(label='복사  (F5)',           command=self.copy_files)
        em.add_command(label='이동  (F6)',           command=self.move_files)
        em.add_command(label='삭제  (F8)',           command=self.delete_files)
        em.add_separator()
        em.add_command(label='이름 바꾸기  (F2)',    command=self.rename_file)
        em.add_command(label='일괄 이름바꾸기',      command=self.batch_rename)
        em.add_separator()
        em.add_command(label='전체 선택  (Ctrl+A)',  command=self._select_all)
        em.add_command(label='선택 반전',            command=self._invert_selection)
        em.add_separator()
        em.add_command(label='경로 복사',            command=self.copy_path)
        em.add_command(label='탐색기에서 열기',      command=self.open_in_explorer)

        vm = add_menu('보기')
        vm.add_checkbutton(label='숨김 파일 표시', variable=self.view_hidden,
                           command=self.refresh_panels)
        vm.add_separator()
        vm.add_command(label='새로고침  (F5)',       command=self.refresh_panels)
        vm.add_separator()
        # 테마 서브메뉴
        tm = tk.Menu(vm, tearoff=0, bg=p['panel_bg'], fg=p['tree_fg'],
                     activebackground=p['accent'], activeforeground=p['accent_fg'],
                     font=(UI_FONT, 9))
        vm.add_cascade(label='테마', menu=tm)
        for tname in THEMES:
            tm.add_command(label=tname, command=lambda t=tname: self.change_theme(t))

        tools = add_menu('도구')
        tools.add_command(label='압축하기  (Ctrl+Z)', command=self.compress_files)
        tools.add_command(label='압축 풀기',          command=self.extract_files)
        tools.add_separator()
        tools.add_command(label='터미널 열기  (F9)',  command=self.open_terminal)
        tools.add_separator()
        tools.add_command(label='파일 검색  (Ctrl+F)', command=self.search_files)

    def _build_toolbar(self):
        p = self.theme
        self._toolbar = tk.Frame(self.root, bg=p['toolbar_bg'],
                                 relief='flat', height=44)
        self._toolbar.pack(fill='x')
        self._toolbar.pack_propagate(False)

        def tbtn(parent, text, cmd, tip='', color=None):
            bg = color or p['btn_bg']
            fg = p['btn_fg']
            b = tk.Button(parent, text=text, command=cmd,
                          bg=bg, fg=fg, relief='flat',
                          font=(UI_FONT, 11), width=3,
                          activebackground=p['accent'],
                          activeforeground=p['accent_fg'],
                          cursor='hand2', bd=0)
            b.pack(side='left', padx=2, pady=6)
            self._create_tooltip(b, tip)
            return b

        tbtn(self._toolbar, '⟳',  self.refresh_panels,       'F5  새로고침')
        tbtn(self._toolbar, '🏠',  self.go_home,              '홈 폴더')
        tbtn(self._toolbar, '⬆',   self.go_up,               '상위 폴더  (Backspace)')
        tbtn(self._toolbar, '←',   self.go_back,             '뒤로  (Alt+←)')
        tbtn(self._toolbar, '→',   self.go_forward,          '앞으로  (Alt+→)')

        tk.Frame(self._toolbar, bg=p['border'], width=1).pack(side='left', fill='y', padx=6, pady=6)

        tbtn(self._toolbar, '📋', self.copy_files,   'F5  복사')
        tbtn(self._toolbar, '✂', self.move_files,   'F6  이동')
        tbtn(self._toolbar, '🗑', self.delete_files, 'F8  삭제')
        tbtn(self._toolbar, '📁', self.new_folder,   'F7  새 폴더')

        tk.Frame(self._toolbar, bg=p['border'], width=1).pack(side='left', fill='y', padx=6, pady=6)

        tbtn(self._toolbar, '📦', self.compress_files, '압축하기')
        tbtn(self._toolbar, '🔓', self.extract_files,  '압축 풀기')
        tbtn(self._toolbar, '⌨',  self.open_terminal,  'F9  터미널')

        # 오른쪽: 테마 + 숨김 + 검색
        right = tk.Frame(self._toolbar, bg=p['toolbar_bg'])
        right.pack(side='right', padx=8)

        tk.Label(right, text='테마:', bg=p['toolbar_bg'],
                 fg=p['toolbar_fg'], font=(UI_FONT, 9)).pack(side='left', padx=(0, 4))
        self._theme_var = tk.StringVar(value=self._theme_name)
        tcb = ttk.Combobox(right, textvariable=self._theme_var,
                           values=list(THEMES.keys()), state='readonly', width=7)
        tcb.pack(side='left')
        tcb.bind('<<ComboboxSelected>>', lambda _: self.change_theme(self._theme_var.get()))

        tk.Frame(right, bg=p['border'], width=1).pack(side='left', fill='y', padx=8, pady=4)

        chk = tk.Checkbutton(right, text='숨김 파일', variable=self.view_hidden,
                             command=self.refresh_panels,
                             bg=p['toolbar_bg'], fg=p['toolbar_fg'],
                             selectcolor=p['toolbar_bg'],
                             activebackground=p['toolbar_bg'],
                             font=(UI_FONT, 9))
        chk.pack(side='left', padx=4)
        self._hidden_chk = chk

        tk.Frame(right, bg=p['border'], width=1).pack(side='left', fill='y', padx=8, pady=4)

        tk.Label(right, text='🔍', bg=p['toolbar_bg'],
                 fg=p['toolbar_fg'], font=(UI_FONT, 11)).pack(side='left')
        self._search_var = tk.StringVar()
        se = tk.Entry(right, textvariable=self._search_var, width=22,
                      font=(UI_FONT, 9), bg=p['entry_bg'], fg=p['entry_fg'],
                      relief='solid', bd=1, insertbackground=p['entry_fg'])
        se.pack(side='left', padx=4)
        se.bind('<Return>', lambda _: self.search_files())
        self._search_entry = se

        tk.Button(right, text='검색', command=self.search_files,
                  bg=p['accent'], fg=p['accent_fg'], relief='flat',
                  font=(UI_FONT, 9), padx=8, cursor='hand2').pack(side='left')

    def _build_function_buttons(self):
        p = self.theme
        bf = tk.Frame(self.root, bg=p['toolbar_bg'], relief='flat', height=40)
        bf.pack(fill='x')
        bf.pack_propagate(False)
        self._func_frame = bf

        buttons = [
            ('F3  뷰어',  self.view_file_internal, '#27AE60'),
            ('F4  편집',  self.edit_file,           '#2980B9'),
            ('F5  복사',  self.copy_files,           '#E67E22'),
            ('F6  이동',  self.move_files,           '#8E44AD'),
            ('F7  새폴더', self.new_folder,          '#16A085'),
            ('F8  삭제',  self.delete_files,         '#C0392B'),
            ('F9  터미널', self.open_terminal,       '#2C3E50'),
        ]
        for label, cmd, color in buttons:
            tk.Button(bf, text=label, command=cmd,
                      bg=color, fg='#FFFFFF', relief='flat',
                      font=(UI_FONT, 8, 'bold'),
                      activebackground=color, activeforeground='#FFFFFF',
                      cursor='hand2').pack(side='left', fill='both',
                                          expand=True, padx=2, pady=5)

    def _build_statusbar(self):
        p = self.theme
        sb = tk.Frame(self.root, bg=p['status_bg'], relief='flat')
        sb.pack(fill='x', side='bottom')
        self._status_lbl = tk.Label(sb, text='준비됨', anchor='w', padx=10,
                                    bg=p['status_bg'], fg=p['status_fg'],
                                    font=(UI_FONT, 8))
        self._status_lbl.pack(side='left', fill='x', expand=True)

        # 디스크 용량 표시
        self._disk_lbl = tk.Label(sb, text='', anchor='e', padx=10,
                                  bg=p['status_bg'], fg=p['status_fg'],
                                  font=(UI_FONT, 8))
        self._disk_lbl.pack(side='right')
        self._update_disk_info()

    def _update_disk_info(self):
        try:
            path = self._active_panel().current_path
            total, used, free = get_disk_usage(path)
            if total > 0:
                pct  = used / total * 100
                text = f'디스크: {format_size(free)} 여유  /  {format_size(total)} 전체  ({pct:.0f}% 사용)'
                self._disk_lbl.config(text=text)
        except Exception:
            pass
        self.root.after(10000, self._update_disk_info)

    def set_status(self, text: str):
        self._status_lbl.config(text=text)
        self._update_disk_info()

    # ── 단축키 ─────────────────────────────────
    def _setup_shortcuts(self):
        binds = [
            ('<F2>',           lambda _: self.rename_file()),
            ('<F3>',           lambda _: self.view_file_internal()),
            ('<F4>',           lambda _: self.edit_file()),
            ('<F5>',           lambda _: self.copy_files()),
            ('<F6>',           lambda _: self.move_files()),
            ('<F7>',           lambda _: self.new_folder()),
            ('<F8>',           lambda _: self.delete_files()),
            ('<F9>',           lambda _: self.open_terminal()),
            ('<BackSpace>',    lambda _: self._active_panel().navigate_up()),
            ('<Alt-Left>',     lambda _: self._active_panel().navigate_back()),
            ('<Alt-Right>',    lambda _: self._active_panel().navigate_forward()),
            ('<Control-r>',    lambda _: self.refresh_panels()),
            ('<Control-a>',    lambda _: self._select_all()),
            ('<Control-f>',    lambda _: self._focus_filter()),
            ('<Control-l>',    lambda _: self._focus_path()),
            ('<Control-t>',    lambda _: self._active_panel().new_tab()),
            ('<Control-w>',    lambda _: self._active_panel().close_tab(
                                    self._active_panel()._cur_tab)),
            ('<Control-Shift-C>', lambda _: self.copy_path()),
        ]
        for key, handler in binds:
            self.root.bind(key, handler)

    # ── 활성 패널 ─────────────────────────────
    def _active_panel(self) -> FilePanel:
        return self.left_panel if self._active_side == 'left' else self.right_panel

    def _opposite_panel(self) -> FilePanel:
        return self.right_panel if self._active_side == 'left' else self.left_panel

    def set_active(self, side: str):
        self._active_side = side

    def _select_all(self):
        self._active_panel()._select_all()

    def _invert_selection(self):
        panel = self._active_panel()
        tree  = panel.tree
        all_items = [i for i in tree.get_children()
                     if panel._strip(tree.item(i)['text']) != '..']
        cur_sel = set(tree.selection())
        tree.selection_set([i for i in all_items if i not in cur_sel])

    def _focus_path(self):
        self._active_panel()._path_entry.focus_set()
        self._active_panel()._path_entry.select_range(0, 'end')

    def _focus_filter(self):
        panel = self._active_panel()
        panel._filter_entry.focus_set()
        panel._filter_entry.select_range(0, 'end')

    # ── 최근 경로 관리 ─────────────────────────
    def add_recent_path(self, path: str):
        if path in self._recent_paths:
            self._recent_paths.remove(path)
        self._recent_paths.insert(0, path)
        if len(self._recent_paths) > RECENT_MAX:
            self._recent_paths = self._recent_paths[:RECENT_MAX]
        self.bookmark_panel.add_recent(path)

    # ── 드래그 앤 드롭 실행 ────────────────────
    def _do_dnd_op(self, src_paths: list, dest: str, op: str, src_panel):
        verb = '복사' if op == 'copy' else '이동'
        if not os.path.isdir(dest):
            return
        if op == 'move':
            src_dir = os.path.dirname(src_paths[0])
            if src_dir == dest:
                return

        dlg   = ProgressDialog(self.root, f'DnD {verb} 중...', self.theme)
        total = len(src_paths)
        success = 0

        def worker():
            nonlocal success
            for idx, src in enumerate(src_paths):
                if dlg.cancelled:
                    break
                fname     = os.path.basename(src)
                dest_file = os.path.join(dest, fname)
                if os.path.exists(dest_file):
                    base, ext = os.path.splitext(fname)
                    cnt = 1
                    while os.path.exists(os.path.join(dest, f'{base}_{verb}{cnt}{ext}')):
                        cnt += 1
                    dest_file = os.path.join(dest, f'{base}_{verb}{cnt}{ext}')
                try:
                    if op == 'copy':
                        shutil.copytree(src, dest_file) if os.path.isdir(src) \
                            else shutil.copy2(src, dest_file)
                    else:
                        shutil.move(src, dest_file)
                    success += 1
                except Exception as e:
                    self.root.after(0, lambda err=str(e), fn=fname:
                        messagebox.showerror('오류', f'{fn}: {err}'))
                self.root.after(0, lambda i=idx+1, n=fname:
                    dlg.update_progress(i, total, n))

            self.root.after(0, lambda: (
                dlg.destroy(),
                self.refresh_panels(),
                self.set_status(f'DnD {verb} 완료: {success}/{total}개')
            ))

        threading.Thread(target=worker, daemon=True).start()

    # ── 탐색 ────────────────────────────────────
    def refresh_panels(self):
        self.left_panel.refresh()
        self.right_panel.refresh()
        self.set_status('새로고침 완료')

    def go_home(self):
        self._active_panel().navigate(str(Path.home()))

    def go_up(self):
        self._active_panel().navigate_up()

    def go_back(self):
        self._active_panel().navigate_back()

    def go_forward(self):
        self._active_panel().navigate_forward()

    # ── 파일 열기 ───────────────────────────────
    def open_file(self, path: str):
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.call(('open', path))
            else:
                subprocess.call(('xdg-open', path))
            self.set_status(f'열기: {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('오류', f'파일을 열 수 없습니다: {e}')

    def view_file_internal(self):
        files = self._active_panel().get_selected_paths()
        if not files:
            messagebox.showwarning('경고', '파일을 선택해주세요.')
            return
        path = files[0]
        if not os.path.isfile(path):
            messagebox.showwarning('경고', '파일만 뷰어로 볼 수 있습니다.')
            return
        ext = os.path.splitext(path)[1].lower()
        if ext in TEXT_EXTS or os.path.getsize(path) < 2 * 1024 * 1024:
            TextViewerDialog(self.root, path, self.theme)
        else:
            self.open_file(path)

    def edit_file(self):
        files = self._active_panel().get_selected_paths()
        if not files:
            messagebox.showwarning('경고', '파일을 선택해주세요.')
            return
        path = files[0]
        if not os.path.isfile(path):
            messagebox.showwarning('경고', '파일만 편집할 수 있습니다.')
            return
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(['notepad.exe', path])
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', '-e', path])
            else:
                for ed in ['gedit', 'kate', 'mousepad', 'xed', 'nano']:
                    if shutil.which(ed):
                        subprocess.Popen([ed, path])
                        break
            self.set_status(f'편집 중: {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('오류', f'편집기를 열 수 없습니다: {e}')

    # ── 파일 작업 ───────────────────────────────
    def _do_file_op(self, op: str):
        """op: 'copy' or 'move'"""
        src_files = self._active_panel().get_selected_paths()
        if not src_files:
            messagebox.showwarning('경고', f'{"복사" if op=="copy" else "이동"}할 파일을 선택하세요.')
            return
        dest = self._opposite_panel().current_path
        if not os.path.isdir(dest):
            messagebox.showerror('오류', '대상 경로가 유효하지 않습니다.')
            return
        if op == 'move':
            src_dir = os.path.dirname(src_files[0])
            if src_dir == dest:
                messagebox.showwarning('경고', '같은 폴더로는 이동할 수 없습니다.')
                return

        verb = '복사' if op == 'copy' else '이동'
        # 확인
        names = [os.path.basename(f) for f in src_files[:5]]
        extra = f'\n... 외 {len(src_files)-5}개' if len(src_files) > 5 else ''
        msg = f'다음 {len(src_files)}개를 {dest} 으로 {verb}하시겠습니까?\n\n' + \
              '\n'.join(f'  • {n}' for n in names) + extra
        if not messagebox.askyesno(f'{verb} 확인', msg):
            return

        dlg = ProgressDialog(self.root, f'{verb} 중...', self.theme)
        total = len(src_files)
        success = 0

        def worker():
            nonlocal success
            for idx, src in enumerate(src_files):
                if dlg.cancelled:
                    break
                fname = os.path.basename(src)
                dest_file = os.path.join(dest, fname)
                # 중복 처리
                if os.path.exists(dest_file):
                    base, ext = os.path.splitext(fname)
                    cnt = 1
                    while os.path.exists(os.path.join(dest, f'{base}_{verb}{cnt}{ext}')):
                        cnt += 1
                    dest_file = os.path.join(dest, f'{base}_{verb}{cnt}{ext}')
                try:
                    if op == 'copy':
                        if os.path.isdir(src):
                            shutil.copytree(src, dest_file)
                        else:
                            shutil.copy2(src, dest_file)
                    else:
                        shutil.move(src, dest_file)
                    success += 1
                except Exception as e:
                    self.root.after(0, lambda err=str(e), fn=fname:
                        messagebox.showerror('오류', f'{fn}: {err}'))
                self.root.after(0, lambda i=idx+1, n=fname:
                    dlg.update_progress(i, total, n))

            self.root.after(0, lambda: (
                dlg.destroy(),
                self.refresh_panels(),
                self.set_status(f'{verb} 완료: {success}/{total}개')
            ))

        threading.Thread(target=worker, daemon=True).start()

    def copy_files(self):
        self._do_file_op('copy')

    def move_files(self):
        self._do_file_op('move')

    def delete_files(self):
        files = self._active_panel().get_selected_paths()
        if not files:
            messagebox.showwarning('경고', '삭제할 파일을 선택해주세요.')
            return
        names = [os.path.basename(f) for f in files[:8]]
        extra = f'\n... 외 {len(files)-8}개' if len(files) > 8 else ''
        msg = f'다음 {len(files)}개를 영구 삭제하시겠습니까?\n\n' + \
              '\n'.join(f'  • {n}' for n in names) + extra + \
              '\n\n이 작업은 되돌릴 수 없습니다.'
        if not messagebox.askyesno('삭제 확인', msg, icon='warning'):
            return
        ok = 0
        for fp in files:
            try:
                shutil.rmtree(fp) if os.path.isdir(fp) else os.remove(fp)
                ok += 1
            except Exception as e:
                messagebox.showerror('오류', f'{os.path.basename(fp)}: {e}')
        self.refresh_panels()
        self.set_status(f'삭제 완료: {ok}/{len(files)}개')

    def new_folder(self):
        path = self._active_panel().current_path
        name = simpledialog.askstring('새 폴더', '폴더 이름을 입력하세요:', parent=self.root)
        if not name:
            return
        try:
            os.makedirs(os.path.join(path, name), exist_ok=False)
            self._active_panel().refresh()
            self.set_status(f'폴더 생성: {name}')
        except FileExistsError:
            messagebox.showerror('오류', '같은 이름의 폴더가 이미 존재합니다.')
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def new_file(self):
        path = self._active_panel().current_path
        name = simpledialog.askstring('새 파일', '파일 이름을 입력하세요:', parent=self.root)
        if not name:
            return
        try:
            with open(os.path.join(path, name), 'w', encoding='utf-8') as _:
                pass
            self._active_panel().refresh()
            self.set_status(f'파일 생성: {name}')
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def rename_file(self):
        files = self._active_panel().get_selected_paths()
        if not files:
            messagebox.showwarning('경고', '이름을 바꿀 파일을 선택해주세요.')
            return
        if len(files) > 1:
            messagebox.showwarning('경고', '단일 이름 변경은 파일 1개만 가능합니다.\n여러 개는 일괄 이름바꾸기를 이용하세요.')
            return
        fp   = files[0]
        old  = os.path.basename(fp)
        new  = simpledialog.askstring('이름 바꾸기', '새 이름을 입력하세요:',
                                      initialvalue=old, parent=self.root)
        if not new or new == old:
            return
        try:
            os.rename(fp, os.path.join(os.path.dirname(fp), new))
            self._active_panel().refresh()
            self.set_status(f'이름 변경: {old} → {new}')
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def batch_rename(self):
        files = self._active_panel().get_selected_paths()
        if len(files) < 2:
            messagebox.showwarning('경고', '일괄 이름바꾸기는 2개 이상 선택해야 합니다.')
            return
        BatchRenameDialog(self.root, files, self.theme,
                          on_done=self._active_panel().refresh)

    def copy_path(self):
        files = self._active_panel().get_selected_paths()
        text  = '\n'.join(files) if files else self._active_panel().current_path
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.set_status(f'경로 복사 완료')
        except Exception:
            pass

    def open_in_explorer(self):
        files  = self._active_panel().get_selected_paths()
        target = files[0] if files else self._active_panel().current_path
        try:
            sys_name = platform.system()
            if sys_name == 'Windows':
                norm = os.path.normpath(target)
                subprocess.Popen(['explorer', '/select,' if os.path.isfile(norm) else '', norm])
            elif sys_name == 'Darwin':
                subprocess.Popen(['open', '-R' if os.path.isfile(target) else '', target])
            else:
                folder = target if os.path.isdir(target) else os.path.dirname(target)
                opener = shutil.which('xdg-open')
                if opener:
                    subprocess.Popen([opener, folder])
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def show_properties(self):
        files = self._active_panel().get_selected_paths()
        if not files:
            messagebox.showwarning('경고', '파일을 선택해주세요.')
            return
        lines = []
        total_size = 0
        for fp in files:
            try:
                st = os.stat(fp)
                is_dir = os.path.isdir(fp)
                lines.append(f'이름:  {os.path.basename(fp)}')
                lines.append(f'경로:  {fp}')
                lines.append(f'종류:  {"폴더" if is_dir else get_file_type(os.path.basename(fp))}')
                if not is_dir:
                    lines.append(f'크기:  {format_size(st.st_size)}')
                    total_size += st.st_size
                lines.append(f'수정:  {datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")}')
                lines.append(f'생성:  {datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S")}')
                lines.append('')
            except Exception as e:
                lines.append(f'오류: {e}\n')
        if len(files) > 1:
            lines.append(f'─ 합계: {len(files)}개  |  {format_size(total_size)} ─')
        messagebox.showinfo('속성', '\n'.join(lines))

    # ── 압축 ────────────────────────────────────
    def compress_files(self):
        import zipfile
        files = self._active_panel().get_selected_paths()
        if not files:
            messagebox.showwarning('경고', '압축할 파일을 선택해주세요.')
            return
        name = simpledialog.askstring('압축하기', '압축 파일 이름:', initialvalue='archive.zip',
                                      parent=self.root)
        if not name:
            return
        if not name.lower().endswith(('.zip','.tar','.gz')):
            name += '.zip'
        dest = os.path.join(self._active_panel().current_path, name)
        try:
            with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fp in files:
                    if os.path.isfile(fp):
                        zf.write(fp, os.path.basename(fp))
                    else:
                        for root, _, fns in os.walk(fp):
                            for fn in fns:
                                full = os.path.join(root, fn)
                                zf.write(full, os.path.relpath(full, os.path.dirname(fp)))
            self._active_panel().refresh()
            self.set_status(f'압축 완료: {name}')
        except Exception as e:
            messagebox.showerror('오류', str(e))

    def extract_files(self):
        import zipfile, tarfile
        files = self._active_panel().get_selected_paths()
        if not files:
            messagebox.showwarning('경고', '압축 파일을 선택해주세요.')
            return
        fp = files[0]
        if not fp.lower().endswith(('.zip','.tar','.gz','.bz2','.xz')):
            messagebox.showwarning('경고', '지원하지 않는 형식입니다.')
            return
        dest = self._active_panel().current_path
        try:
            if fp.lower().endswith('.zip'):
                with zipfile.ZipFile(fp, 'r') as zf:
                    zf.extractall(dest)
            else:
                with tarfile.open(fp, 'r:*') as tf:
                    tf.extractall(dest)
            self._active_panel().refresh()
            self.set_status('압축 풀기 완료')
        except Exception as e:
            messagebox.showerror('오류', str(e))

    # ── 터미널 ─────────────────────────────────
    def open_terminal(self):
        path = self._active_panel().current_path
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(['cmd.exe'], cwd=path)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', '-a', 'Terminal', path])
            else:
                for term in ['gnome-terminal','konsole','xterm','xfce4-terminal']:
                    if shutil.which(term):
                        subprocess.Popen([term], cwd=path)
                        break
            self.set_status(f'터미널: {path}')
        except Exception as e:
            messagebox.showerror('오류', str(e))

    # ── 검색 ────────────────────────────────────
    def search_files(self):
        query = self._search_var.get().strip()
        if not query:
            self._search_entry.focus_set()
            return
        search_path = self._active_panel().current_path

        # 검색 중 커서 표시
        self.root.config(cursor='watch')
        self.root.update()

        results = []
        # 확장자 필터 판별
        q_lower = query.lower()
        is_ext   = q_lower.startswith('.') and ' ' not in q_lower and '*' not in q_lower
        is_glob  = '*' in q_lower or '?' in q_lower

        try:
            for root_dir, dirs, files in os.walk(search_path):
                if not self.view_hidden.get():
                    dirs[:]  = [d for d in dirs  if not d.startswith('.')]
                    files    = [f for f in files if not f.startswith('.')]
                for name in dirs + files:
                    nl = name.lower()
                    if is_ext:
                        match = nl.endswith(q_lower)
                    elif is_glob:
                        match = fnmatch.fnmatch(nl, q_lower)
                    else:
                        match = q_lower in nl
                    if match:
                        results.append(os.path.join(root_dir, name))
                    if len(results) >= 2000:
                        break
                if len(results) >= 2000:
                    break
        except Exception as e:
            messagebox.showerror('오류', str(e))
        finally:
            self.root.config(cursor='')

        self._show_search_results(query, results, search_path)

    def _show_search_results(self, query: str, results: list, base_path: str):
        p = self.theme
        dlg = tk.Toplevel(self.root)
        limit_note = '  [최대 2,000개 표시]' if len(results) >= 2000 else ''
        dlg.title(f'검색 결과: "{query}"  ({len(results)}개{limit_note})')
        dlg.geometry('860x560')
        dlg.configure(bg=p['main_bg'])
        dlg.transient(self.root)

        # 헤더
        hdr = tk.Frame(dlg, bg=p['toolbar_bg'], pady=6)
        hdr.pack(fill='x')
        tk.Label(hdr,
                 text=f'🔍  "{query}"  —  {len(results)}개 결과  |  범위: {base_path}',
                 bg=p['toolbar_bg'], fg=p['toolbar_fg'],
                 font=(UI_FONT, 9, 'bold')).pack(side='left', padx=12)

        # 힌트: 와일드카드/확장자 설명
        hint = tk.Label(hdr, text='💡 팁: *.py / .mp4 / ??파일 형식 지원',
                        bg=p['toolbar_bg'], fg=p['crumb_sep'],
                        font=(UI_FONT, 8))
        hint.pack(side='right', padx=12)

        # 트리
        frame = tk.Frame(dlg, bg=p['panel_bg'])
        frame.pack(fill='both', expand=True, padx=8, pady=8)
        columns = ('path', 'type', 'size', 'date')
        tree = ttk.Treeview(frame, columns=columns, show='tree headings', height=18)
        tree.heading('#0',     text='이름')
        tree.heading('path',   text='경로')
        tree.heading('type',   text='종류')
        tree.heading('size',   text='크기')
        tree.heading('date',   text='수정 날짜')
        tree.column('#0',    width=220)
        tree.column('path',  width=280)
        tree.column('type',  width=80, anchor='center')
        tree.column('size',  width=80, anchor='e')
        tree.column('date',  width=130)
        sb = ttk.Scrollbar(frame, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        for fp in results:
            name  = os.path.basename(fp)
            icon  = '📁' if os.path.isdir(fp) else get_file_icon(name)
            rel   = os.path.relpath(fp, base_path)
            ftype = '폴더' if os.path.isdir(fp) else get_file_type(name)
            try:
                st   = os.stat(fp)
                size = '' if os.path.isdir(fp) else format_size(st.st_size)
                date = datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')
            except Exception:
                size, date = '', ''
            tree.insert('', 'end', text=f'{icon}  {name}',
                        values=(rel, ftype, size, date))

        def _get_sel_path():
            sel = tree.selection()
            if not sel:
                return None
            return results[tree.index(sel[0])]

        def on_open_active(event=None):
            fp = _get_sel_path()
            if fp is None:
                return
            if os.path.isdir(fp):
                self._active_panel().navigate(fp)
            else:
                self.open_file(fp)
            dlg.destroy()

        def on_open_opposite(event=None):
            fp = _get_sel_path()
            if fp is None:
                return
            target = os.path.dirname(fp) if os.path.isfile(fp) else fp
            self._opposite_panel().navigate(target)
            dlg.destroy()

        tree.bind('<Double-Button-1>', on_open_active)
        tree.bind('<Return>',          on_open_active)

        bf = tk.Frame(dlg, bg=p['main_bg'])
        bf.pack(fill='x', padx=8, pady=(0, 8))
        tk.Button(bf, text='활성 패널에서 열기', command=on_open_active,
                  bg=p['accent'], fg=p['accent_fg'], relief='flat',
                  font=(UI_FONT, 9), padx=14, pady=3, cursor='hand2').pack(side='left', padx=4)
        tk.Button(bf, text='반대 패널에서 열기', command=on_open_opposite,
                  bg=p['btn_bg'], fg=p['btn_fg'], relief='flat',
                  font=(UI_FONT, 9), padx=14, pady=3, cursor='hand2').pack(side='left', padx=4)
        tk.Button(bf, text='닫기', command=dlg.destroy,
                  bg='#7F8C8D', fg='#FFFFFF', relief='flat',
                  font=(UI_FONT, 9), padx=14, pady=3, cursor='hand2').pack(side='right', padx=4)

        self.set_status(f'검색 완료: "{query}"  {len(results)}개 결과')

    # ── 드라이브 선택 (Windows) ──────────────────
    def select_drive(self, side: str):
        if platform.system() != 'Windows':
            return
        import string, ctypes
        drives = []
        for d in string.ascii_uppercase:
            dp = f'{d}:\\'
            if os.path.exists(dp):
                try:
                    dt = ctypes.windll.kernel32.GetDriveTypeW(dp)
                    types = {2:'이동식',3:'고정',4:'네트워크',5:'CD-ROM',6:'RAM'}
                    buf = ctypes.create_unicode_buffer(1024)
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        dp, buf, ctypes.sizeof(buf), None, None, None, None, 0)
                    label = buf.value
                    _, _, free = get_disk_usage(dp)
                    display = f'{dp}  {label}  [{types.get(dt,"?")}]  여유 {format_size(free)}'
                    drives.append((dp, display))
                except Exception:
                    drives.append((dp, dp))

        if not drives:
            return
        p = self.theme
        dlg = tk.Toplevel(self.root)
        dlg.title('드라이브 선택')
        dlg.geometry('480x360')
        dlg.configure(bg=p['main_bg'])
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text='드라이브를 선택하세요',
                 bg=p['toolbar_bg'], fg=p['toolbar_fg'],
                 font=(UI_FONT, 10, 'bold'), pady=8).pack(fill='x')

        lb_frame = tk.Frame(dlg, bg=p['panel_bg'])
        lb_frame.pack(fill='both', expand=True, padx=12, pady=8)
        sb = tk.Scrollbar(lb_frame)
        sb.pack(side='right', fill='y')
        lb = tk.Listbox(lb_frame, yscrollcommand=sb.set,
                        bg=p['tree_bg'], fg=p['tree_fg'],
                        selectbackground=p['accent'], selectforeground=p['accent_fg'],
                        font=(UI_FONT, 10), relief='flat', activestyle='none')
        sb.config(command=lb.yview)
        lb.pack(fill='both', expand=True)
        for _, disp in drives:
            lb.insert('end', disp)

        def select():
            sel = lb.curselection()
            if sel:
                dp = drives[sel[0]][0]
                panel = self.left_panel if side == 'left' else self.right_panel
                panel.navigate(dp)
                dlg.destroy()

        lb.bind('<Double-Button-1>', lambda _: select())
        bf = tk.Frame(dlg, bg=p['main_bg'])
        bf.pack(fill='x', padx=12, pady=(0, 10))
        tk.Button(bf, text='선택', command=select,
                  bg=p['accent'], fg=p['accent_fg'], relief='flat',
                  font=(UI_FONT, 9), padx=16, pady=3, cursor='hand2').pack(side='left', padx=4)
        tk.Button(bf, text='취소', command=dlg.destroy,
                  bg='#7F8C8D', fg='#FFFFFF', relief='flat',
                  font=(UI_FONT, 9), padx=16, pady=3, cursor='hand2').pack(side='left', padx=4)

    # ── 테마 변경 ────────────────────────────────
    def change_theme(self, name: str):
        if name not in THEMES:
            return
        self._theme_name = name
        self.theme = THEMES[name]
        self._apply_ttk_style()

        p = self.theme
        self.root.configure(bg=p['main_bg'])
        self._toolbar.configure(bg=p['toolbar_bg'])
        self._func_frame.configure(bg=p['toolbar_bg'])

        # 상태바
        for w in self.root.winfo_children():
            if isinstance(w, tk.Frame) and w not in (self._toolbar, self._func_frame):
                try:
                    w.configure(bg=p['main_bg'])
                except Exception:
                    pass

        self._status_lbl.configure(bg=p['status_bg'], fg=p['status_fg'])
        self._disk_lbl.configure(bg=p['status_bg'], fg=p['status_fg'])
        self.left_panel.apply_theme(p)
        self.right_panel.apply_theme(p)
        self.bookmark_panel.apply_theme(p)
        self._theme_var.set(name)
        self.set_status(f'테마 변경: {name}')

    # ── 툴팁 ────────────────────────────────────
    def _create_tooltip(self, widget, text: str):
        tip = [None]
        def enter(e):
            t = tk.Toplevel()
            t.wm_overrideredirect(True)
            t.wm_geometry(f'+{e.x_root+14}+{e.y_root+12}')
            tk.Label(t, text=text, bg='#FFFFCC', fg='#333333',
                     relief='solid', bd=1, padx=5, pady=2,
                     font=(UI_FONT, 8)).pack()
            tip[0] = t
        def leave(e):
            if tip[0]:
                tip[0].destroy()
                tip[0] = None
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)


# ─── 진입점 ──────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default='')
    except Exception:
        pass
    app = SimpleCommander(root)
    root.mainloop()

if __name__ == '__main__':
    main()
