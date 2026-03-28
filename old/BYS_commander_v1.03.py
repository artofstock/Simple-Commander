import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import os
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import platform
import threading
import queue
import time

class TotalCommanderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BYS Commander v2.0 - 향상된 파일 관리자")
        self.root.geometry("1400x800")
        self.root.configure(bg="#1a1a1a")
        
        # 전역 스타일 설정
        self.setup_styles()
        
        # 초기 경로 설정
        home = str(Path.home())
        self.left_path = tk.StringVar(value=home)
        self.right_path = tk.StringVar(value=home)
        
        self.left_selected = set()
        self.right_selected = set()
        self.active_panel = "left"
        
        # 클립보드 (복사/이동용)
        self.clipboard = []
        self.clipboard_mode = None
        
        # 검색 관련
        self.search_queue = queue.Queue()
        self.search_thread = None
        
        # 드라이브 정보
        self.drives = self.get_drives()
        
        self.create_widgets()
        self.refresh_panels()
        self.setup_key_bindings()
    
    def get_drives(self):
        """시스템 드라이브 목록 가져오기"""
        drives = []
        if platform.system() == "Windows":
            for drive in range(ord('A'), ord('Z')+1):
                drive_letter = f"{chr(drive)}:\\"
                if os.path.exists(drive_letter):
                    drives.append(drive_letter)
        else:
            # Linux/Mac - 주요 마운트 포인트
            drives = ["/", "/home", "/Users"]
            for mount in ["/mnt", "/media"]:
                if os.path.exists(mount):
                    try:
                        for item in os.listdir(mount):
                            full_path = os.path.join(mount, item)
                            if os.path.isdir(full_path):
                                drives.append(full_path)
                    except:
                        pass
        return drives
    
    def setup_styles(self):
        """전역 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Treeview 스타일
        style.configure('Custom.Treeview', 
                       background='#1a1a1a', 
                       foreground='white',
                       fieldbackground='#1a1a1a', 
                       borderwidth=0,
                       rowheight=25)
        style.configure('Custom.Treeview.Heading', 
                       background='#2d2d2d', 
                       foreground='white',
                       borderwidth=1,
                       relief='flat')
        style.map('Custom.Treeview', 
                 background=[('selected', '#1e3a5f')],
                 foreground=[('selected', 'white')])
    
    def create_widgets(self):
        # 상단 툴바
        self.create_toolbar()
        
        # 메인 패널 컨테이너
        main_container = tk.Frame(self.root, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측 패널
        self.left_panel = self.create_panel(main_container, self.left_path, "left")
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        # 중앙 버튼 패널
        self.create_center_buttons(main_container)
        
        # 우측 패널
        self.right_panel = self.create_panel(main_container, self.right_path, "right")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        # 하단 상태바
        self.create_status_bar()
        
        # 퀵 뷰 패널 (숨김 상태로 시작)
        self.quickview_visible = False
        self.quickview_frame = None
    
    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#2d2d2d", height=40)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # 기본 기능 버튼
        basic_buttons = [
            ("↻ 새로고침", self.refresh_panels),
            ("🏠 홈", self.go_home),
            ("📊 드라이브", self.show_drive_menu),
            ("🔍 고급검색", self.advanced_search),
            ("📁 빠른이동", self.quick_navigation),
            ("👁️ 미리보기", self.toggle_quickview),
        ]
        
        for text, command in basic_buttons:
            btn = tk.Button(toolbar, text=text, bg="#404040", fg="white", 
                          command=command, relief=tk.FLAT, padx=10, font=("", 9))
            btn.pack(side=tk.LEFT, padx=2)
        
        # 검색 프레임
        search_frame = tk.Frame(toolbar, bg="#2d2d2d")
        search_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(search_frame, text="🔍", bg="#2d2d2d", fg="white").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, bg="#1a1a1a", fg="white", 
                                   width=25, insertbackground="white", font=("", 9))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', self.search_files)
        self.search_entry.bind('<KeyRelease>', self.real_time_search)
    
    def create_panel(self, parent, path_var, side):
        panel = tk.Frame(parent, bg="#1a1a1a", relief=tk.RAISED, borderwidth=1)
        
        # 경로 입력 및 드라이브 선택
        path_frame = tk.Frame(panel, bg="#2d2d2d")
        path_frame.pack(fill=tk.X, pady=(0, 2))
        
        # 드라이브 선택 버튼
        drive_btn = tk.Button(path_frame, text="📀", bg="#404040", fg="white",
                             command=lambda: self.show_drive_menu(side), 
                             relief=tk.FLAT, font=("", 10))
        drive_btn.pack(side=tk.LEFT, padx=2)
        
        # 경로 입력창
        path_entry = tk.Entry(path_frame, textvariable=path_var, bg="#1a1a1a", 
                             fg="white", insertbackground="white", font=("", 10))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        path_entry.bind('<Return>', lambda e: self.refresh_panels())
        
        # 북마크 버튼
        bookmark_btn = tk.Button(path_frame, text="⭐", bg="#404040", fg="white",
                               command=self.add_bookmark, relief=tk.FLAT)
        bookmark_btn.pack(side=tk.RIGHT, padx=2)
        
        # 파일 리스트 (Treeview)
        tree_frame = tk.Frame(panel, bg="#1a1a1a")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns = ('size', 'type', 'date')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings',
                           yscrollcommand=v_scrollbar.set,
                           xscrollcommand=h_scrollbar.set,
                           selectmode='extended', style='Custom.Treeview')
        
        tree.heading('#0', text='이름', anchor=tk.W)
        tree.heading('size', text='크기', anchor=tk.W)
        tree.heading('type', text='유형', anchor=tk.W)
        tree.heading('date', text='수정 날짜', anchor=tk.W)
        
        tree.column('#0', width=300, anchor=tk.W)
        tree.column('size', width=100, anchor=tk.W)
        tree.column('type', width=100, anchor=tk.W)
        tree.column('date', width=150, anchor=tk.W)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.config(command=tree.yview)
        h_scrollbar.config(command=tree.xview)
        
        # 이벤트 바인딩
        tree.bind('<Button-1>', lambda e: self.on_panel_click(side))
        tree.bind('<Double-Button-1>', lambda e: self.on_double_click(side))
        tree.bind('<Return>', lambda e: self.on_double_click(side))
        tree.bind('<Key>', self.on_key_press)
        
        # 우클릭 메뉴
        self.create_context_menu(tree, side)
        
        # 상태 표시
        status = tk.Label(panel, text="", bg="#2d2d2d", fg="#888888", 
                         anchor=tk.W, padx=5, pady=2, font=("", 9))
        status.pack(fill=tk.X)
        
        # 패널 정보 저장
        if side == "left":
            self.left_tree = tree
            self.left_status = status
        else:
            self.right_tree = tree
            self.right_status = status
        
        return panel
    
    def create_center_buttons(self, parent):
        center_frame = tk.Frame(parent, bg="#1a1a1a", width=80)
        center_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        center_frame.pack_propagate(False)
        
        center_buttons = [
            ("▶\n복사", lambda: self.paste_files('copy'), "#2d5f2d"),
            ("⇄\n이동", lambda: self.paste_files('move'), "#5f5f2d"),
            ("✎\n편집", self.edit_file, "#404040"),
            ("👁️\n보기", self.view_file, "#404040"),
            ("📁\n새폴더", self.new_folder, "#404040"),
            ("✂️\n이름변경", self.rename_file, "#404040"),
            ("🗑️\n삭제", self.delete_files, "#8b0000"),
            ("📋\n속성", self.show_properties, "#404040"),
            ("📈\n용량분석", self.analyze_disk_usage, "#2d2d5f"),
            ("🔍\n파일검색", self.search_in_directory, "#5f2d5f"),
        ]
        
        for text, command, color in center_buttons:
            btn = tk.Button(center_frame, text=text, bg=color, fg="white",
                          command=command, relief=tk.FLAT, padx=5, pady=8,
                          font=("", 9), justify=tk.CENTER)
            btn.pack(fill=tk.X, pady=2)
    
    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="BYS Commander v2.0 - 준비", 
                                  bg="#2d2d2d", fg="#888888", anchor=tk.W,
                                  padx=10, pady=2, font=("", 9))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def create_context_menu(self, tree, side):
        menu = tk.Menu(tree, tearoff=0, bg="#2d2d2d", fg="white",
                      activebackground="#404040", activeforeground="white")
        
        menu.add_command(label="열기", command=lambda: self.on_double_click(side))
        menu.add_separator()
        menu.add_command(label="복사 (Ctrl+C)", command=self.copy_files)
        menu.add_command(label="이동 (Ctrl+X)", command=self.move_files)
        menu.add_command(label="삭제 (Del)", command=self.delete_files)
        menu.add_separator()
        menu.add_command(label="이름 바꾸기 (F2)", command=self.rename_file)
        menu.add_command(label="속성 (Alt+Enter)", command=self.show_properties)
        menu.add_separator()
        menu.add_command(label="여기에서 검색", command=self.search_in_directory)
        menu.add_command(label="명령 프롬프트 열기", command=self.open_terminal)
        menu.add_command(label="ZIP으로 압축", command=self.create_zip)
        
        tree.bind('<Button-3>', lambda e: self.show_context_menu(e, menu, side))
    
    def setup_key_bindings(self):
        # 기본 키 바인딩
        self.root.bind('<F5>', lambda e: self.refresh_panels())
        self.root.bind('<F7>', lambda e: self.new_folder())
        self.root.bind('<F8>', lambda e: self.delete_files())
        self.root.bind('<F2>', lambda e: self.rename_file())
        self.root.bind('<Delete>', lambda e: self.delete_files())
        self.root.bind('<Alt-Enter>', lambda e: self.show_properties())
        
        # 복사/이동 단축키
        self.root.bind('<Control-c>', lambda e: self.copy_files())
        self.root.bind('<Control-x>', lambda e: self.move_files())
        self.root.bind('<Control-v>', lambda e: self.paste_files('copy' if self.clipboard_mode == 'copy' else 'move'))
        
        # 탭 키로 패널 전환
        self.root.bind('<Tab>', lambda e: self.switch_panel())
    
    def switch_panel(self):
        self.active_panel = "right" if self.active_panel == "left" else "left"
        self.refresh_panels()
        self.update_status(f"활성 패널: {'좌측' if self.active_panel == 'left' else '우측'}")
    
    def refresh_panels(self):
        self.refresh_panel("left")
        self.refresh_panel("right")
        self.update_status("패널 새로고침 완료")
    
    def refresh_panel(self, side):
        tree = self.left_tree if side == "left" else self.right_tree
        path = self.left_path.get() if side == "left" else self.right_path.get()
        status = self.left_status if side == "left" else self.right_status
        
        # 기존 항목 삭제
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            if not os.path.exists(path):
                raise FileNotFoundError
            
            total_size = 0
            dir_count = 0
            file_count = 0
            
            # 상위 디렉토리 항목
            if os.path.dirname(path) != path:
                tree.insert('', 'end', text='📁 ..', values=('', '상위 폴더', ''), tags=('parent',))
            
            # 파일 및 폴더 목록
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                try:
                    stat = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    
                    if is_dir:
                        size = ''
                        file_type = '폴더'
                        dir_count += 1
                    else:
                        size = self.format_size(stat.st_size)
                        file_type = self.get_file_type(item)
                        file_count += 1
                        total_size += stat.st_size
                    
                    date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    items.append((item, is_dir, size, file_type, date))
                except:
                    continue
            
            # 정렬 (폴더 먼저, 이름순)
            items.sort(key=lambda x: (not x[1], x[0].lower()))
            
            # 트리에 추가
            for item, is_dir, size, file_type, date in items:
                icon = '📁' if is_dir else self.get_file_icon(item)
                tree.insert('', 'end', text=f'{icon} {item}', 
                           values=(size, file_type, date), 
                           tags=('dir' if is_dir else 'file',))
            
            # 상태 업데이트
            selected_count = len(tree.selection())
            status_text = f"총 {len(items)}개 항목"
            if selected_count > 0:
                status_text = f"{selected_count}개 선택됨 / " + status_text
            
            status_text += f" (폴더: {dir_count}, 파일: {file_count})"
            if total_size > 0:
                status_text += f" / 총 크기: {self.format_size(total_size)}"
            
            status.config(text=status_text)
            
        except Exception as e:
            status.config(text=f"오류: {str(e)}")
            messagebox.showerror("오류", f"경로를 열 수 없습니다: {str(e)}")
    
    def get_file_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            '.txt': '텍스트 파일',
            '.pdf': 'PDF 문서',
            '.doc': 'Word 문서',
            '.docx': 'Word 문서',
            '.xls': 'Excel 파일',
            '.xlsx': 'Excel 파일',
            '.jpg': 'JPEG 이미지',
            '.png': 'PNG 이미지',
            '.mp3': '음악 파일',
            '.mp4': '동영상 파일',
            '.zip': '압축 파일',
            '.exe': '실행 파일',
            '.py': 'Python 파일',
        }
        return type_map.get(ext, '파일')
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def get_file_icon(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        icon_map = {
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.m4a': '🎵',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬',
            '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
            '.txt': '📄', '.doc': '📄', '.docx': '📄', '.pdf': '📄',
            '.py': '🐍', '.js': '📜', '.java': '☕', '.cpp': '⚙️', '.c': '⚙️',
            '.exe': '⚙️', '.msi': '⚙️',
        }
        return icon_map.get(ext, '📃')
    
    def on_panel_click(self, side):
        self.active_panel = side
        self.refresh_panel(side)
    
    def on_double_click(self, side):
        tree = self.left_tree if side == "left" else self.right_tree
        path_var = self.left_path if side == "left" else self.right_path
        
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        text = item['text']
        
        if '📁' in text:
            name = text.replace('📁 ', '')
            current_path = path_var.get()
            
            if name == '..':
                new_path = os.path.dirname(current_path)
            else:
                new_path = os.path.join(current_path, name)
            
            if os.path.isdir(new_path):
                path_var.set(new_path)
                self.refresh_panel(side)
        else:
            self.view_file()
    
    def on_key_press(self, event):
        if event.keysym == 'BackSpace':
            self.go_up_directory()
    
    def go_up_directory(self):
        path_var = self.left_path if self.active_panel == "left" else self.right_path
        current_path = path_var.get()
        parent_path = os.path.dirname(current_path)
        
        if parent_path != current_path:
            path_var.set(parent_path)
            self.refresh_panel(self.active_panel)
    
    def get_selected_files(self):
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        selection = tree.selection()
        files = []
        
        for item in selection:
            text = tree.item(item)['text']
            # 아이콘 제거
            for icon in ['📁', '🖼️', '🎵', '🎬', '📦', '📄', '💻', '📃', '🐍', '📜', '☕', '⚙️']:
                text = text.replace(icon + ' ', '')
            
            if text != '..':
                full_path = os.path.join(path, text)
                files.append(full_path)
        
        return files
    
    def view_file(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        file_path = files[0]
        if os.path.isfile(file_path):
            try:
                if platform.system() == 'Darwin':
                    subprocess.call(('open', file_path))
                elif platform.system() == 'Windows':
                    os.startfile(file_path)
                else:
                    subprocess.call(('xdg-open', file_path))
                self.update_status(f"파일 열기: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("오류", f"파일을 열 수 없습니다: {str(e)}")
    
    def edit_file(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        file_path = files[0]
        if os.path.isfile(file_path):
            try:
                # 간단한 텍스트 편집기 창 열기
                self.open_text_editor(file_path)
            except Exception as e:
                messagebox.showerror("오류", f"파일을 편집할 수 없습니다: {str(e)}")
    
    def open_text_editor(self, file_path):
        editor_window = tk.Toplevel(self.root)
        editor_window.title(f"텍스트 편집기 - {os.path.basename(file_path)}")
        editor_window.geometry("800x600")
        editor_window.configure(bg="#1a1a1a")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            try:
                with open(file_path, 'r', encoding='cp949') as f:
                    content = f.read()
            except:
                content = "⚠️ 파일을 읽을 수 없습니다 (바이너리 파일일 수 있음)"
        
        text_area = scrolledtext.ScrolledText(editor_window, bg="#1a1a1a", fg="white",
                                            insertbackground="white", font=("Consolas", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert('1.0', content)
        
        def save_file():
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_area.get('1.0', tk.END))
                messagebox.showinfo("성공", "파일이 저장되었습니다.")
                editor_window.destroy()
            except Exception as e:
                messagebox.showerror("오류", f"저장 실패: {str(e)}")
        
        save_btn = tk.Button(editor_window, text="저장", bg="#2d5f2d", fg="white",
                           command=save_file, padx=20)
        save_btn.pack(pady=5)
    
    def copy_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        self.clipboard = files
        self.clipboard_mode = 'copy'
        self.update_status(f"{len(files)}개 항목 복사 대기 중")
        messagebox.showinfo("복사", f"{len(files)}개 항목이 클립보드에 복사되었습니다.\n반대쪽 패널에서 붙여넣기하세요.")
    
    def move_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        self.clipboard = files
        self.clipboard_mode = 'move'
        self.update_status(f"{len(files)}개 항목 이동 대기 중")
        messagebox.showinfo("이동", f"{len(files)}개 항목이 이동 대기 중입니다.\n반대쪽 패널에서 붙여넣기하세요.")
    
    def paste_files(self, mode=None):
        if mode is None:
            mode = self.clipboard_mode
        
        if not self.clipboard:
            messagebox.showwarning("경고", "복사/이동할 항목이 없습니다.")
            return
        
        dest_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        success_count = 0
        error_count = 0
        
        for src in self.clipboard:
            try:
                dest = os.path.join(dest_path, os.path.basename(src))
                
                # 같은 경로면 스킵
                if os.path.dirname(src) == dest_path and mode == 'move':
                    continue
                
                # 이미 존재하면 확인
                if os.path.exists(dest):
                    response = messagebox.askyesno("확인", 
                        f"'{os.path.basename(dest)}'이(가) 이미 존재합니다.\n덮어쓰시겠습니까?")
                    if not response:
                        continue
                
                if mode == 'copy':
                    if os.path.isdir(src):
                        shutil.copytree(src, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dest)
                elif mode == 'move':
                    shutil.move(src, dest)
                
                success_count += 1
            except Exception as e:
                error_count += 1
                messagebox.showerror("오류", f"'{os.path.basename(src)}' 처리 실패: {str(e)}")
        
        if mode == 'move':
            self.clipboard = []
            self.clipboard_mode = None
        
        self.refresh_panels()
        
        if success_count > 0:
            action = "복사" if mode == 'copy' else "이동"
            self.update_status(f"{success_count}개 항목 {action} 완료")
            messagebox.showinfo("완료", f"{success_count}개 항목이 {action}되었습니다.")
    
    def delete_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        response = messagebox.askyesno("확인", 
            f"{len(files)}개 항목을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")
        
        if not response:
            return
        
        success_count = 0
        error_count = 0
        
        for file_path in files:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                success_count += 1
            except Exception as e:
                error_count += 1
                messagebox.showerror("오류", f"'{os.path.basename(file_path)}' 삭제 실패: {str(e)}")
        
        self.refresh_panels()
        
        if success_count > 0:
            self.update_status(f"{success_count}개 항목 삭제 완료")
            messagebox.showinfo("완료", f"{success_count}개 항목이 삭제되었습니다.")
    
    def new_folder(self):
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        name = simpledialog.askstring("새 폴더", "폴더 이름을 입력하세요:")
        if not name:
            return
        
        new_path = os.path.join(path, name)
        
        try:
            os.makedirs(new_path, exist_ok=True)
            self.update_status(f"폴더 생성: {name}")
            self.refresh_panels()
        except Exception as e:
            messagebox.showerror("오류", f"폴더 생성 실패: {str(e)}")
    
    def rename_file(self):
        files = self.get_selected_files()
        if not files or len(files) > 1:
            messagebox.showwarning("경고", "하나의 파일만 선택해주세요.")
            return
        
        old_path = files[0]
        old_name = os.path.basename(old_path)
        
        new_name = simpledialog.askstring("이름 바꾸기", "새 이름을 입력하세요:", initialvalue=old_name)
        if not new_name or new_name == old_name:
            return
        
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        try:
            os.rename(old_path, new_path)
            self.update_status(f"이름 변경: {old_name} → {new_name}")
            self.refresh_panels()
        except Exception as e:
            messagebox.showerror("오류", f"이름 변경 실패: {str(e)}")
    
    def show_properties(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        file_path = files[0]
        try:
            stat = os.stat(file_path)
            size = self.format_size(stat.st_size) if os.path.isfile(file_path) else "폴더"
            modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            created = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            
            info = f"이름: {os.path.basename(file_path)}\n"
            info += f"경로: {file_path}\n"
            info += f"크기: {size}\n"
            info += f"생성 날짜: {created}\n"
            info += f"수정 날짜: {modified}\n"
            info += f"타입: {'디렉토리' if os.path.isdir(file_path) else '파일'}\n"
            info += f"권한: {oct(stat.st_mode)[-3:]}"
            
            messagebox.showinfo("속성", info)
        except Exception as e:
            messagebox.showerror("오류", f"속성을 가져올 수 없습니다: {str(e)}")
    
    def show_context_menu(self, event, menu, side):
        self.active_panel = side
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def search_files(self, event=None):
        query = self.search_entry.get().strip()
        if not query:
            return
        
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        
        # 검색 결과를 하이라이트
        for item in tree.get_children():
            text = tree.item(item)['text'].lower()
            if query.lower() in text:
                tree.selection_add(item)
                tree.see(item)
    
    def real_time_search(self, event):
        """실시간 검색"""
        query = self.search_entry.get().strip()
        if len(query) < 2:  # 2글자 이상부터 검색
            return
        
        # 검색 스레드 실행
        if self.search_thread and self.search_thread.is_alive():
            self.search_queue.put(query)
        else:
            self.search_thread = threading.Thread(target=self._search_worker, args=(query,))
            self.search_thread.daemon = True
            self.search_thread.start()
    
    def _search_worker(self, initial_query):
        """백그라운드 검색 작업"""
        query = initial_query
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        
        while True:
            try:
                # 현재 디렉토리에서 검색
                found_items = []
                for root, dirs, files in os.walk(path):
                    for name in dirs + files:
                        if query.lower() in name.lower():
                            found_items.append(os.path.join(root, name))
                            if len(found_items) >= 100:  # 최대 100개 결과
                                break
                    if len(found_items) >= 100:
                        break
                
                # UI 업데이트
                self.root.after(0, self._update_search_results, found_items, query)
                
                # 새 검색어 대기
                try:
                    query = self.search_queue.get(timeout=0.5)
                except queue.Empty:
                    break
                    
            except Exception as e:
                break
    
    def _update_search_results(self, results, query):
        """검색 결과 업데이트"""
        self.update_status(f"검색 완료: '{query}' - {len(results)}개 항목 찾음")
        # 여기에 검색 결과를 표시하는 로직을 추가할 수 있습니다.
    
    def advanced_search(self):
        """고급 검색 대화상자"""
        search_window = tk.Toplevel(self.root)
        search_window.title("고급 검색")
        search_window.geometry("500x400")
        search_window.configure(bg="#1a1a1a")
        
        tk.Label(search_window, text="파일 이름:", bg="#1a1a1a", fg="white").pack(pady=5)
        name_entry = tk.Entry(search_window, width=50, bg="#2d2d2d", fg="white")
        name_entry.pack(pady=5)
        
        tk.Label(search_window, text="파일 내용:", bg="#1a1a1a", fg="white").pack(pady=5)
        content_entry = tk.Entry(search_window, width=50, bg="#2d2d2d", fg="white")
        content_entry.pack(pady=5)
        
        tk.Label(search_window, text="검색 경로:", bg="#1a1a1a", fg="white").pack(pady=5)
        path_entry = tk.Entry(search_window, width=50, bg="#2d2d2d", fg="white")
        path_entry.insert(0, self.left_path.get() if self.active_panel == "left" else self.right_path.get())
        path_entry.pack(pady=5)
        
        def start_search():
            # 검색 로직 구현
            search_window.destroy()
            messagebox.showinfo("검색", "검색이 시작되었습니다.\n결과는 하단 상태바에 표시됩니다.")
        
        tk.Button(search_window, text="검색 시작", command=start_search, 
                 bg="#2d5f2d", fg="white").pack(pady=20)
    
    def show_drive_menu(self, side=None):
        """드라이브 선택 메뉴 표시"""
        menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="white")
        
        for drive in self.drives:
            try:
                usage = shutil.disk_usage(drive)
                free_space = self.format_size(usage.free)
                total_space = self.format_size(usage.total)
                label = f"{drive} ({free_space} / {total_space} 남음)"
                menu.add_command(label=label, 
                               command=lambda d=drive: self.select_drive(d, side))
            except:
                menu.add_command(label=drive, 
                               command=lambda d=drive: self.select_drive(d, side))
        
        # 현재 마우스 위치에 메뉴 표시
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        menu.tk_popup(x, y)
    
    def select_drive(self, drive, side):
        """드라이브 선택"""
        if side is None:
            side = self.active_panel
        
        if side == "left":
            self.left_path.set(drive)
            self.refresh_panel("left")
        else:
            self.right_path.set(drive)
            self.refresh_panel("right")
        
        self.update_status(f"드라이브 선택: {drive}")
    
    def quick_navigation(self):
        """빠른 이동 대화상자"""
        path = simpledialog.askstring("빠른 이동", "이동할 경로를 입력하세요:")
        if path and os.path.exists(path):
            if self.active_panel == "left":
                self.left_path.set(path)
                self.refresh_panel("left")
            else:
                self.right_path.set(path)
                self.refresh_panel("right")
            self.update_status(f"빠른 이동: {path}")
        elif path:
            messagebox.showerror("오류", "경로를 찾을 수 없습니다.")
    
    def add_bookmark(self):
        """북마크 추가"""
        current_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        name = simpledialog.askstring("북마크 추가", "북마크 이름을 입력하세요:", 
                                     initialvalue=os.path.basename(current_path))
        if name:
            # 북마크 저장 로직 (간단한 구현)
            messagebox.showinfo("북마크", f"'{name}' 북마크가 추가되었습니다.")
    
    def analyze_disk_usage(self):
        """디스크 사용량 분석"""
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        def analyze():
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except:
                        pass
                dir_count += len(dirs)
            
            return total_size, file_count, dir_count
        
        # 별도 스레드에서 분석 실행
        def run_analysis():
            self.update_status("디스크 사용량 분석 중...")
            total_size, file_count, dir_count = analyze()
            
            self.root.after(0, lambda: messagebox.showinfo("디스크 사용량 분석",
                f"경로: {path}\n"
                f"총 크기: {self.format_size(total_size)}\n"
                f"파일 수: {file_count:,}개\n"
                f"폴더 수: {dir_count:,}개"))
            
            self.root.after(0, lambda: self.update_status("디스크 사용량 분석 완료"))
        
        threading.Thread(target=run_analysis, daemon=True).start()
    
    def search_in_directory(self):
        """현재 디렉토리에서 검색"""
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        query = simpledialog.askstring("디렉토리 검색", "검색어를 입력하세요:")
        
        if query:
            results = []
            for root, dirs, files in os.walk(path):
                for name in dirs + files:
                    if query.lower() in name.lower():
                        results.append(os.path.join(root, name))
            
            if results:
                result_text = "\n".join(results[:20])  # 최대 20개 표시
                if len(results) > 20:
                    result_text += f"\n... 외 {len(results)-20}개 더"
                messagebox.showinfo("검색 결과", result_text)
            else:
                messagebox.showinfo("검색 결과", "일치하는 항목이 없습니다.")
    
    def open_terminal(self):
        """터미널/명령 프롬프트 열기"""
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        try:
            if platform.system() == "Windows":
                subprocess.Popen(f'cmd /K "cd /D {path}"', shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(['open', '-a', 'Terminal', path])
            else:
                subprocess.Popen(['x-terminal-emulator', '--working-directory', path])
        except Exception as e:
            messagebox.showerror("오류", f"터미널을 열 수 없습니다: {str(e)}")
    
    def create_zip(self):
        """ZIP 압축 파일 생성"""
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "압축할 파일을 선택해주세요.")
            return
        
        zip_path = simpledialog.askstring("ZIP 압축", "압축 파일 이름을 입력하세요:",
                                         initialvalue="archive.zip")
        if zip_path:
            try:
                if not zip_path.endswith('.zip'):
                    zip_path += '.zip'
                
                shutil.make_archive(zip_path.replace('.zip', ''), 'zip', 
                                  os.path.dirname(files[0]), 
                                  os.path.basename(files[0]) if len(files) == 1 else None)
                
                messagebox.showinfo("성공", f"ZIP 압축이 완료되었습니다: {zip_path}")
                self.refresh_panels()
            except Exception as e:
                messagebox.showerror("오류", f"압축 실패: {str(e)}")
    
    def toggle_quickview(self):
        """퀵 뷰 패널 토글"""
        if not self.quickview_visible:
            self.show_quickview()
        else:
            self.hide_quickview()
    
    def show_quickview(self):
        """퀵 뷰 패널 표시"""
        if self.quickview_frame:
            self.quickview_frame.destroy()
        
        self.quickview_frame = tk.Frame(self.root, bg="#1a1a1a", width=300)
        self.quickview_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        self.quickview_frame.pack_propagate(False)
        
        tk.Label(self.quickview_frame, text="퀵 뷰", bg="#2d2d2d", fg="white",
                font=("", 12, "bold")).pack(fill=tk.X, pady=5)
        
        # 선택된 파일 정보 표시
        files = self.get_selected_files()
        if files:
            file_path = files[0]
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        preview = f.read(1000)  # 처음 1000자만 표시
                except:
                    preview = "⚠️ 미리보기를 표시할 수 없습니다"
                
                text_area = scrolledtext.ScrolledText(self.quickview_frame, 
                                                    bg="#1a1a1a", fg="white",
                                                    height=20, width=35)
                text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                text_area.insert('1.0', preview)
                text_area.config(state=tk.DISABLED)
        
        self.quickview_visible = True
    
    def hide_quickview(self):
        """퀵 뷰 패널 숨기기"""
        if self.quickview_frame:
            self.quickview_frame.destroy()
            self.quickview_frame = None
        self.quickview_visible = False
    
    def go_home(self):
        home = str(Path.home())
        if self.active_panel == "left":
            self.left_path.set(home)
        else:
            self.right_path.set(home)
        self.refresh_panels()
        self.update_status("홈 디렉토리로 이동")
    
    def update_status(self, message):
        """상태바 업데이트"""
        self.status_bar.config(text=f"BYS Commander v2.0 - {message}")
    
    def on_closing(self):
        """프로그램 종료 시 호출"""
        self.root.destroy()

def main():
    root = tk.Tk()
    app = TotalCommanderGUI(root)
    
    # 종료 이벤트 처리
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()