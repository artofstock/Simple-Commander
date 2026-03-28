import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import platform

class TotalCommanderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("토탈커맨더 스타일 파일 매니저")
        self.root.geometry("1400x800")
        self.root.configure(bg="#f0f0f0")
        
        # 전역 스타일 설정 (먼저 설정)
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
        self.clipboard_mode = None  # 'copy' or 'move'
        self.clipboard_origin = None  # 'left' or 'right' - panel where copy/move originated
        
        # 히스토리
        self.left_history = [home]
        self.right_history = [home]
        self.left_history_index = 0
        self.right_history_index = 0
        
        # 뷰 옵션
        self.view_hidden = tk.BooleanVar(value=False)
        
        self.create_widgets()
        self.refresh_panels()
        
    def setup_styles(self):
        """전역 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Treeview 스타일 - 밝은 테마
        style.configure('Treeview', 
                       background='white', 
                       foreground='#333333',
                       fieldbackground='white', 
                       borderwidth=1,
                       relief='solid',
                       rowheight=28)
        style.configure('Treeview.Heading', 
                       background='#e0e0e0', 
                       foreground='#333333',
                       borderwidth=1,
                       relief='raised',
                       font=('Arial', 9, 'bold'))
        style.map('Treeview', 
                 background=[('selected', '#0078d7')],
                 foreground=[('selected', 'white')])
        
        # Scrollbar 스타일
        style.configure('Vertical.TScrollbar',
                       background='#d0d0d0',
                       troughcolor='#f0f0f0',
                       borderwidth=1,
                       arrowcolor='#333333')
    
    def create_widgets(self):
        # 메뉴바
        self.create_menubar()
        
        # 상단 툴바
        toolbar = tk.Frame(self.root, bg="#e8e8e8", height=50, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(fill=tk.X, padx=0, pady=0)
        
        # 툴바 버튼들
        btn_frame = tk.Frame(toolbar, bg="#e8e8e8")
        btn_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        toolbar_buttons = [
            ("↻", self.refresh_panels, "새로고침 (F5)"),
            ("🏠", self.go_home, "홈"),
            ("⬆", self.go_up, "상위 폴더"),
            ("←", lambda: self.navigate_history("back"), "뒤로"),
            ("→", lambda: self.navigate_history("forward"), "앞으로"),
        ]
        
        for text, command, tooltip in toolbar_buttons:
            btn = tk.Button(btn_frame, text=text, command=command, 
                          bg="#f5f5f5", fg="#333333", relief=tk.RAISED,
                          font=('Arial', 12), width=3, height=1,
                          borderwidth=1, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2)
            self.create_tooltip(btn, tooltip)
        
        # 구분선
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 뷰 옵션
        view_frame = tk.Frame(toolbar, bg="#e8e8e8")
        view_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(view_frame, text="보기:", bg="#e8e8e8", fg="#333333").pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(view_frame, text="숨김 파일", variable=self.view_hidden,
                      command=self.refresh_panels, bg="#e8e8e8", 
                      activebackground="#e8e8e8", fg="#333333").pack(side=tk.LEFT)
        
        # 검색 박스
        search_frame = tk.Frame(toolbar, bg="#e8e8e8")
        search_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(search_frame, text="🔍", bg="#e8e8e8", fg="#333333", font=('Arial', 12)).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, bg="white", fg="#333333", width=25,
                                     relief=tk.SOLID, borderwidth=1)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', self.search_files)
        tk.Button(search_frame, text="검색", command=self.search_files,
                 bg="#0078d7", fg="white", relief=tk.RAISED, borderwidth=1,
                 cursor="hand2").pack(side=tk.LEFT)
        
        # 메인 패널 컨테이너
        main_container = tk.Frame(self.root, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측 패널
        self.left_panel = self.create_panel(main_container, self.left_path, "left")
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))
        
        # 우측 패널
        self.right_panel = self.create_panel(main_container, self.right_path, "right")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(3, 0))
        
        # 하단 기능 버튼
        self.create_function_buttons()
        
        # 상태바
        self.create_statusbar()
    
    def create_menubar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="새 폴더 (F7)", command=self.new_folder)
        file_menu.add_command(label="새 파일", command=self.new_file)
        file_menu.add_separator()
        file_menu.add_command(label="속성", command=self.show_properties)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.root.quit)
        
        # 편집 메뉴
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="편집", menu=edit_menu)
        edit_menu.add_command(label="복사 (F5)", command=self.copy_files)
        edit_menu.add_command(label="이동 (F6)", command=self.move_files)
        edit_menu.add_command(label="삭제 (F8)", command=self.delete_files)
        edit_menu.add_separator()
        edit_menu.add_command(label="이름 바꾸기", command=self.rename_file)
        edit_menu.add_command(label="전체 선택 (Ctrl+A)", command=self.select_all)
        edit_menu.add_command(label="선택 반전", command=self.invert_selection)
        
        # 보기 메뉴
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="보기", menu=view_menu)
        view_menu.add_checkbutton(label="숨김 파일", variable=self.view_hidden,
                                 command=self.refresh_panels)
        view_menu.add_separator()
        view_menu.add_command(label="새로고침 (F5)", command=self.refresh_panels)
        
        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도구", menu=tools_menu)
        tools_menu.add_command(label="압축하기", command=self.compress_files)
        tools_menu.add_command(label="압축 풀기", command=self.extract_files)
        tools_menu.add_separator()
        tools_menu.add_command(label="터미널 열기", command=self.open_terminal)
    
    def create_panel(self, parent, path_var, side):
        panel = tk.Frame(parent, bg="#f0f0f0", relief=tk.RAISED, borderwidth=2)
        
        # 경로 입력
        path_frame = tk.Frame(panel, bg="#d0d0d0", relief=tk.RAISED, borderwidth=1)
        path_frame.pack(fill=tk.X, pady=(0, 2))
        
        tk.Label(path_frame, text="📂", bg="#d0d0d0", fg="#333333", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        path_entry = tk.Entry(path_frame, textvariable=path_var, bg="white", 
                             fg="#333333", relief=tk.SOLID, borderwidth=1,
                             font=('Arial', 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        path_entry.bind('<Return>', lambda e: self.change_directory(side))
        
        # 드라이브 선택 버튼 (Windows)
        if platform.system() == 'Windows':
            drive_btn = tk.Button(path_frame, text="💾", command=lambda: self.select_drive(side),
                                bg="#f5f5f5", relief=tk.RAISED, borderwidth=1, cursor="hand2")
            drive_btn.pack(side=tk.RIGHT, padx=5)
        
        # 파일 리스트 (Treeview)
        tree_frame = tk.Frame(panel, bg="white")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ('size', 'date', 'type')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings',
                           yscrollcommand=scrollbar.set, selectmode='extended')
        
        tree.heading('#0', text='이름')
        tree.heading('size', text='크기')
        tree.heading('date', text='수정 날짜')
        tree.heading('type', text='종류')
        
        tree.column('#0', width=350, minwidth=150)
        tree.column('size', width=100, minwidth=80)
        tree.column('date', width=150, minwidth=120)
        tree.column('type', width=100, minwidth=80)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)
        
        # 이벤트 바인딩
        tree.bind('<FocusIn>', lambda e: self.on_panel_focus(side))
        tree.bind('<Double-Button-1>', lambda e: self.on_double_click(side))
        tree.bind('<Return>', lambda e: self.on_double_click(side))
        tree.bind('<Control-a>', lambda e: self.select_all())
        tree.bind('<Control-c>', lambda e: self.copy_files())
        tree.bind('<Control-x>', lambda e: self.move_files())
        tree.bind('<Control-v>', lambda e: self.paste_files(self.clipboard_mode if self.clipboard_mode else 'copy'))
        tree.bind('<Delete>', lambda e: self.delete_files())
        tree.bind('<space>', lambda e: self.toggle_selection(side))
        tree.bind('<<TreeviewSelect>>', lambda e: self.on_selection_change(side))
        
        # 우클릭 메뉴
        menu = tk.Menu(tree, tearoff=0, bg="white", fg="#333333",
                      activebackground="#0078d7", activeforeground="white",
                      borderwidth=1, relief=tk.RAISED)
        menu.add_command(label="열기", command=lambda: self.on_double_click(side))
        menu.add_separator()
        menu.add_command(label="복사 (F5)", command=self.copy_files)
        menu.add_command(label="이동 (F6)", command=self.move_files)
        menu.add_command(label="삭제 (F8)", command=self.delete_files)
        menu.add_separator()
        menu.add_command(label="이름 바꾸기", command=self.rename_file)
        menu.add_command(label="속성", command=self.show_properties)
        
        tree.bind('<Button-3>', lambda e: self.show_context_menu(e, menu, side))
        
        # 상태 표시
        status = tk.Label(panel, text="", bg="#d0d0d0", fg="#333333", 
                         anchor=tk.W, padx=5, pady=3, relief=tk.SUNKEN, borderwidth=1,
                         font=('Arial', 9))
        status.pack(fill=tk.X)
        
        # 패널 정보 저장
        if side == "left":
            self.left_tree = tree
            self.left_status = status
        else:
            self.right_tree = tree
            self.right_status = status
        
        return panel
    
    def create_function_buttons(self):
        button_frame = tk.Frame(self.root, bg="#e8e8e8", relief=tk.RAISED, borderwidth=1)
        button_frame.pack(fill=tk.X, padx=0, pady=0)
        
        buttons = [
            ("F3\n보기", self.view_file, "#4CAF50"),
            ("F4\n편집", self.edit_file, "#2196F3"),
            ("F5\n복사", self.copy_files, "#FF9800"),
            ("F6\n이동", self.move_files, "#9C27B0"),
            ("F7\n새폴더", self.new_folder, "#00BCD4"),
            ("F8\n삭제", self.delete_files, "#F44336"),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, bg=color, fg="white",
                          command=command, relief=tk.RAISED, font=('Arial', 9, 'bold'),
                          borderwidth=2, cursor="hand2", height=2)
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, pady=5)
            
            # 키 바인딩
            key = text.split()[0].lower()
            self.root.bind(f'<{key.upper()}>', lambda e, c=command: c())
    
    def create_statusbar(self):
        statusbar = tk.Frame(self.root, bg="#e8e8e8", relief=tk.SUNKEN, borderwidth=1)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.statusbar_label = tk.Label(statusbar, text="준비됨", bg="#e8e8e8", 
                                        fg="#333333", anchor=tk.W, padx=10, pady=3,
                                        font=('Arial', 9))
        self.statusbar_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def create_tooltip(self, widget, text):
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, bg="#ffffcc", fg="#333333",
                           relief=tk.SOLID, borderwidth=1, padx=5, pady=2,
                           font=('Arial', 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def refresh_panels(self):
        self.refresh_panel("left")
        self.refresh_panel("right")
    
    def refresh_panel(self, side):
        tree = self.left_tree if side == "left" else self.right_tree
        path = self.left_path.get() if side == "left" else self.right_path.get()
        status = self.left_status if side == "left" else self.right_status
        
        # 현재 선택 상태 저장
        current_selection = tree.selection()
        selected_items = []
        for item in current_selection:
            item_text = tree.item(item)['text']
            selected_items.append(item_text)
        
        # 기존 항목 삭제
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            if not os.path.exists(path):
                raise FileNotFoundError
            
            # 상위 디렉토리 항목
            if os.path.dirname(path) != path:  # 루트가 아닐 때만
                tree.insert('', 'end', text='📁 ..', values=('', '', '상위 폴더'), tags=('parent',))
            
            # 파일 및 폴더 목록
            items = []
            for item in os.listdir(path):
                # 숨김 파일 필터링
                if not self.view_hidden.get() and item.startswith('.'):
                    continue
                
                full_path = os.path.join(path, item)
                try:
                    stat = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    size = self.format_size(stat.st_size) if not is_dir else ''
                    date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    file_type = '폴더' if is_dir else self.get_file_type(item)
                    items.append((item, is_dir, size, date, file_type))
                except:
                    continue
            
            # 폴더 먼저, 이름순 정렬
            items.sort(key=lambda x: (not x[1], x[0].lower()))
            
            # 트리에 추가하고 이전 선택 복원
            new_selection = []
            for item, is_dir, size, date, file_type in items:
                icon = '📁' if is_dir else self.get_file_icon(item)
                item_text = f'{icon} {item}'
                iid = tree.insert('', 'end', text=item_text, 
                           values=(size, date, file_type), 
                           tags=('dir' if is_dir else 'file',))
                
                # 이전에 선택되었던 항목이면 다시 선택
                if item_text in selected_items:
                    new_selection.append(iid)
            
            # 선택 복원
            if new_selection:
                tree.selection_set(new_selection)
            
            # 상태 업데이트
            selected_count = len(new_selection)
            if selected_count > 0:
                status.config(text=f"{selected_count}개 선택됨 / 총 {len(items)}개 항목")
            else:
                status.config(text=f"{len(items)}개 항목")
            
            self.statusbar_label.config(text=f"현재 위치: {path}")
            
        except Exception as e:
            messagebox.showerror("오류", f"경로를 열 수 없습니다: {str(e)}")
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def get_file_icon(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico']:
            return '🖼️'
        elif ext in ['.mp3', '.wav', '.flac', '.m4a', '.ogg']:
            return '🎵'
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
            return '🎬'
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return '📦'
        elif ext in ['.txt', '.doc', '.docx', '.odt']:
            return '📄'
        elif ext in ['.pdf']:
            return '📕'
        elif ext in ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css']:
            return '💻'
        elif ext in ['.xlsx', '.xls', '.csv']:
            return '📊'
        elif ext in ['.ppt', '.pptx']:
            return '📽️'
        else:
            return '📃'
    
    def get_file_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        types = {
            '.txt': '텍스트', '.pdf': 'PDF', '.doc': 'Word', '.docx': 'Word',
            '.jpg': '이미지', '.png': '이미지', '.gif': '이미지',
            '.mp3': '음악', '.wav': '음악', '.mp4': '비디오', '.avi': '비디오',
            '.zip': '압축', '.rar': '압축', '.py': 'Python', '.js': 'JavaScript'
        }
        return types.get(ext, '파일')
    
    def on_panel_focus(self, side):
        """패널이 포커스를 받을 때"""
        self.active_panel = side
    
    def on_selection_change(self, side):
        """선택이 변경될 때"""
        tree = self.left_tree if side == "left" else self.right_tree
        status = self.left_status if side == "left" else self.right_status
        
        selected_count = len(tree.selection())
        all_count = len([item for item in tree.get_children() if '..' not in tree.item(item)['text']])
        
        if selected_count > 0:
            status.config(text=f"{selected_count}개 선택됨 / 총 {all_count}개 항목")
        else:
            status.config(text=f"{all_count}개 항목")
    
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
                self.add_to_history(side, new_path)
                self.refresh_panel(side)
        else:
            # 파일 열기
            self.view_file()
    
    def change_directory(self, side):
        path_var = self.left_path if side == "left" else self.right_path
        new_path = path_var.get()
        
        if os.path.isdir(new_path):
            self.add_to_history(side, new_path)
            self.refresh_panel(side)
        else:
            messagebox.showerror("오류", "유효하지 않은 경로입니다.")
    
    def add_to_history(self, side, path):
        if side == "left":
            self.left_history = self.left_history[:self.left_history_index + 1]
            self.left_history.append(path)
            self.left_history_index = len(self.left_history) - 1
        else:
            self.right_history = self.right_history[:self.right_history_index + 1]
            self.right_history.append(path)
            self.right_history_index = len(self.right_history) - 1
    
    def navigate_history(self, direction):
        if self.active_panel == "left":
            history = self.left_history
            index = self.left_history_index
            path_var = self.left_path
        else:
            history = self.right_history
            index = self.right_history_index
            path_var = self.right_path
        
        if direction == "back" and index > 0:
            index -= 1
        elif direction == "forward" and index < len(history) - 1:
            index += 1
        else:
            return
        
        if self.active_panel == "left":
            self.left_history_index = index
        else:
            self.right_history_index = index
        
        path_var.set(history[index])
        self.refresh_panel(self.active_panel)

    def go_home(self):
        home = str(Path.home())
        if self.active_panel == "left":
            self.left_path.set(home)
            self.add_to_history("left", home)
        else:
            self.right_path.set(home)
            self.add_to_history("right", home)
        self.refresh_panels()
        
    def go_up(self):
        path_var = self.left_path if self.active_panel == "left" else self.right_path
        current = path_var.get()
        parent = os.path.dirname(current)
        
        if parent != current:
            path_var.set(parent)
            self.add_to_history(self.active_panel, parent)
            self.refresh_panel(self.active_panel)
    
    def select_drive(self, side):
        if platform.system() != 'Windows':
            messagebox.showinfo("안내", "이 기능은 Windows에서만 사용할 수 있습니다.")
            return
        
        import string
        drives = []
        
        # 사용 가능한 드라이브 검색
        for d in string.ascii_uppercase:
            drive_path = f"{d}:\\"
            if os.path.exists(drive_path):
                try:
                    # 드라이브 정보 가져오기
                    import ctypes
                    
                    # 드라이브 타입 확인
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                    type_names = {
                        0: "알 수 없음",
                        1: "존재하지 않음",
                        2: "이동식",
                        3: "고정",
                        4: "네트워크",
                        5: "CD-ROM",
                        6: "RAM 디스크"
                    }
                    
                    # 볼륨 레이블 가져오기
                    volumeNameBuffer = ctypes.create_unicode_buffer(1024)
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        drive_path, volumeNameBuffer, 
                        ctypes.sizeof(volumeNameBuffer), 
                        None, None, None, None, 0
                    )
                    volume_name = volumeNameBuffer.value
                    
                    # 드라이브 정보 저장
                    if volume_name:
                        display_name = f"{drive_path} [{volume_name}] - {type_names.get(drive_type, '알 수 없음')}"
                    else:
                        display_name = f"{drive_path} - {type_names.get(drive_type, '알 수 없음')}"
                    
                    drives.append((drive_path, display_name))
                except:
                    drives.append((drive_path, drive_path))
        
        if not drives:
            messagebox.showwarning("경고", "사용 가능한 드라이브가 없습니다.")
            return
        
        # 드라이브 선택 대화상자
        dialog = tk.Toplevel(self.root)
        dialog.title("드라이브 선택")
        dialog.geometry("500x450")
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 리스트박스
        frame = tk.Frame(dialog, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, font=('Arial', 10), yscrollcommand=scrollbar.set)
        listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for drive_path, display_name in drives:
            listbox.insert(tk.END, display_name)
        
        # 더블클릭으로 선택
        def on_double_click(event):
            select()
        
        listbox.bind('<Double-Button-1>', on_double_click)
        
        # 버튼 프레임
        button_frame = tk.Frame(dialog, bg="white")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def select():
            selection = listbox.curselection()
            if selection:
                drive_path = drives[selection[0]][0]
                if side == "left":
                    self.left_path.set(drive_path)
                    self.add_to_history("left", drive_path)
                    self.refresh_panel("left")
                else:
                    self.right_path.set(drive_path)
                    self.add_to_history("right", drive_path)
                    self.refresh_panel("right")
                dialog.destroy()
        
        tk.Button(button_frame, text="선택", command=select, 
                 bg="#0078d7", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="취소", command=dialog.destroy,
                 bg="#666666", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)

    
    def get_selected_files(self):
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        selection = tree.selection()
        files = []
        
        for item in selection:
            text = tree.item(item)['text']
            # 아이콘 제거
            for icon in ['📁', '🖼️', '🎵', '🎬', '📦', '📄', '💻', '📃', '📕', '📊', '📽️']:
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
                if platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', file_path))
                elif platform.system() == 'Windows':
                    os.startfile(file_path)
                else:  # Linux
                    subprocess.call(('xdg-open', file_path))
                self.statusbar_label.config(text=f"파일 열기: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("오류", f"파일을 열 수 없습니다: {str(e)}")
        elif os.path.isdir(file_path):
            # 폴더인 경우 해당 폴더로 이동
            if self.active_panel == "left":
                self.left_path.set(file_path)
            else:
                self.right_path.set(file_path)
            self.add_to_history(self.active_panel, file_path)
            self.refresh_panel(self.active_panel)

    
    def edit_file(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        file_path = files[0]
        if not os.path.isfile(file_path):
            messagebox.showwarning("경고", "파일만 편집할 수 있습니다.")
            return
        
        try:
            if platform.system() == 'Windows':
                # Windows에서 notepad으로 열기
                subprocess.Popen(['notepad.exe', file_path])
            elif platform.system() == 'Darwin':  # macOS
                # macOS에서 TextEdit으로 열기
                subprocess.Popen(['open', '-a', 'TextEdit', file_path])
            else:  # Linux
                # Linux에서 사용 가능한 편집기 찾기
                editors = ['gedit', 'kate', 'nano', 'vim', 'vi']
                opened = False
                for editor in editors:
                    try:
                        if editor in ['nano', 'vim', 'vi']:
                            # 터미널 필요한 편집기
                            terminals = ['gnome-terminal', 'konsole', 'xterm']
                            for term in terminals:
                                try:
                                    subprocess.Popen([term, '-e', editor, file_path])
                                    opened = True
                                    break
                                except:
                                    continue
                        else:
                            # GUI 편집기
                            subprocess.Popen([editor, file_path])
                            opened = True
                        if opened:
                            break
                    except:
                        continue
                
                if not opened:
                    messagebox.showerror("오류", "사용 가능한 텍스트 편집기를 찾을 수 없습니다.")
                    return
            
            self.statusbar_label.config(text=f"편집 중: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("오류", f"파일을 편집할 수 없습니다: {str(e)}")

    
    def copy_files(self):
        files = self.get_selected_files()
        # fallback: if nothing selected in active panel, try the opposite panel
        if not files:
            prev_panel = self.active_panel
            other = 'right' if prev_panel == 'left' else 'left'
            self.active_panel = other
            files = self.get_selected_files()
            if not files:
                # restore and warn
                self.active_panel = prev_panel
                messagebox.showwarning("경고", "파일을 선택해주세요.")
                return

        self.clipboard = files
        self.clipboard_mode = 'copy'
        self.clipboard_origin = self.active_panel
        self.statusbar_label.config(text=f"{len(files)}개 항목 복사됨 - 대상 패널에서 F5를 눌러 붙여넣기")

    def move_files(self):
        files = self.get_selected_files()
        # fallback to opposite panel if nothing selected in current active panel
        if not files:
            prev_panel = self.active_panel
            other = 'right' if prev_panel == 'left' else 'left'
            self.active_panel = other
            files = self.get_selected_files()
            if not files:
                self.active_panel = prev_panel
                messagebox.showwarning("경고", "파일을 선택해주세요.")
                return

        self.clipboard = files
        self.clipboard_mode = 'move'
        self.clipboard_origin = self.active_panel
        self.statusbar_label.config(text=f"{len(files)}개 항목 이동 대기 - 대상 패널에서 F6를 눌러 이동")

    def paste_files(self, mode=None):
        # determine mode: explicit arg > clipboard_mode > default 'copy'
        if mode is None:
            mode = self.clipboard_mode if self.clipboard_mode else 'copy'

        if not self.clipboard:
            messagebox.showwarning("경고", "복사/이동할 항목이 없습니다.")
            return
        # 원본 경로 확인
        src_path = os.path.dirname(self.clipboard[0])

        # 대상 경로: 기본적으로 복사/이동을 시작한 반대 패널로 지정
        origin = getattr(self, 'clipboard_origin', None)
        if origin == 'left':
            dest_path = self.right_path.get()
        elif origin == 'right':
            dest_path = self.left_path.get()
        else:
            # fallback: 현재 활성 패널
            dest_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        # 같은 경로에 복사/이동하려는 경우 경고
        if src_path == dest_path:
            messagebox.showwarning("경고", "같은 폴더에는 복사/이동할 수 없습니다.\n반대쪽 패널을 선택해주세요.")
            return
        
        success_count = 0
        error_count = 0
        
        for src in self.clipboard:
            try:
                dest = os.path.join(dest_path, os.path.basename(src))
                
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
        
        # 클립보드 초기화 (이동의 경우)
        if mode == 'move':
            self.clipboard = []
            self.clipboard_mode = None
            self.clipboard_origin = None
        
        self.refresh_panels()
        
        if success_count > 0:
            action = "복사" if mode == 'copy' else "이동"
            self.statusbar_label.config(text=f"{success_count}개 항목이 {action}되었습니다.")
            # 복사/이동 성공 후 클립보드 초기화 for copy as well
            if mode == 'copy':
                self.clipboard = []
                self.clipboard_mode = None
                self.clipboard_origin = None
    
    def delete_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        file_list = "\n".join([os.path.basename(f) for f in files[:5]])
        if len(files) > 5:
            file_list += f"\n... 외 {len(files) - 5}개"
        
        response = messagebox.askyesno("확인", 
            f"다음 항목을 삭제하시겠습니까?\n\n{file_list}\n\n이 작업은 되돌릴 수 없습니다.")
        
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
            self.statusbar_label.config(text=f"{success_count}개 항목이 삭제되었습니다.")
    
    def new_folder(self):
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        name = simpledialog.askstring("새 폴더", "폴더 이름을 입력하세요:")
        if not name:
            return
        
        new_path = os.path.join(path, name)
        
        try:
            os.makedirs(new_path)
            self.statusbar_label.config(text=f"'{name}' 폴더가 생성되었습니다.")
            self.refresh_panels()
        except Exception as e:
            messagebox.showerror("오류", f"폴더 생성 실패: {str(e)}")
    
    def new_file(self):
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        # 파일명 입력 대화상자
        dialog = tk.Toplevel(self.root)
        dialog.title("새 파일")
        dialog.geometry("400x150")
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="파일 이름:", bg="white", fg="#333333",
                font=('Arial', 10)).pack(anchor=tk.W, pady=(0, 5))
        
        entry = tk.Entry(frame, font=('Arial', 10), width=40)
        entry.pack(fill=tk.X, pady=(0, 10))
        entry.focus()
        
        def create():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("경고", "파일 이름을 입력해주세요.", parent=dialog)
                return
            
            new_path = os.path.join(path, name)
            
            if os.path.exists(new_path):
                messagebox.showerror("오류", "이미 존재하는 파일명입니다.", parent=dialog)
                return
            
            try:
                with open(new_path, 'w', encoding='utf-8') as f:
                    pass
                self.statusbar_label.config(text=f"'{name}' 파일이 생성되었습니다.")
                self.refresh_panels()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("오류", f"파일 생성 실패: {str(e)}", parent=dialog)
        
        entry.bind('<Return>', lambda e: create())
        
        button_frame = tk.Frame(frame, bg="white")
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="만들기", command=create,
                 bg="#0078d7", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="취소", command=dialog.destroy,
                 bg="#666666", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
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
            self.statusbar_label.config(text=f"'{old_name}'이(가) '{new_name}'(으)로 변경되었습니다.")
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
            is_dir = os.path.isdir(file_path)
            
            # 속성 다이얼로그
            dialog = tk.Toplevel(self.root)
            dialog.title("속성")
            dialog.geometry("400x300")
            dialog.configure(bg="white")
            
            frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            properties = [
                ("이름:", os.path.basename(file_path)),
                ("경로:", os.path.dirname(file_path)),
                ("종류:", "폴더" if is_dir else self.get_file_type(file_path)),
                ("크기:", "폴더" if is_dir else self.format_size(stat.st_size)),
                ("생성:", datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')),
                ("수정:", datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')),
            ]
            
            for i, (label, value) in enumerate(properties):
                tk.Label(frame, text=label, bg="white", fg="#333333", 
                        font=('Arial', 10, 'bold'), anchor=tk.W).grid(row=i, column=0, sticky=tk.W, pady=5)
                tk.Label(frame, text=value, bg="white", fg="#666666", 
                        font=('Arial', 10), anchor=tk.W, wraplength=250).grid(row=i, column=1, sticky=tk.W, pady=5, padx=10)
            
            tk.Button(dialog, text="확인", command=dialog.destroy, 
                     bg="#0078d7", fg="white", font=('Arial', 10),
                     padx=20, pady=5).pack(pady=10)
            
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
            messagebox.showwarning("경고", "검색어를 입력해주세요.")
            return
        
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        
        # 모든 선택 해제
        for item in tree.selection():
            tree.selection_remove(item)
        
        # 검색 결과를 선택
        found_items = []
        query_lower = query.lower()
        
        for item in tree.get_children():
            text = tree.item(item)['text'].lower()
            # 아이콘 제거 후 검색
            for icon in ['📁', '🖼️', '🎵', '🎬', '📦', '📄', '💻', '📃', '📕', '📊', '📽️']:
                text = text.replace(icon.lower() + ' ', '')
            
            if query_lower in text:
                found_items.append(item)
        
        if found_items:
            # 찾은 항목들 선택
            tree.selection_set(found_items)
            # 첫 번째 항목으로 스크롤
            tree.see(found_items[0])
            tree.focus(found_items[0])
            
            self.statusbar_label.config(text=f"'{query}' 검색 결과: {len(found_items)}개 항목")
        else:
            self.statusbar_label.config(text=f"'{query}' 검색 결과 없음")
            messagebox.showinfo("검색", f"'{query}'와 일치하는 항목이 없습니다.")
    
    def select_all(self):
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        
        items_to_select = []
        for item in tree.get_children():
            text = tree.item(item)['text']
            if '..' not in text:  # 상위 폴더는 제외
                items_to_select.append(item)
        
        tree.selection_set(items_to_select)
        self.refresh_panel(self.active_panel)
    
    def toggle_selection(self, side):
        """스페이스바로 개별 아이템 선택/해제"""
        tree = self.left_tree if side == "left" else self.right_tree
        
        # 현재 포커스된 아이템
        focused = tree.focus()
        if focused:
            if focused in tree.selection():
                tree.selection_remove(focused)
            else:
                tree.selection_add(focused)
            
            # 다음 아이템으로 포커스 이동
            children = tree.get_children()
            current_index = children.index(focused)
            if current_index < len(children) - 1:
                next_item = children[current_index + 1]
                tree.focus(next_item)
                tree.see(next_item)
        
        self.refresh_panel(side)
        return "break"  # 기본 동작 방지
    
    def invert_selection(self):
        """선택 반전"""
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        
        currently_selected = set(tree.selection())
        all_items = []
        
        for item in tree.get_children():
            text = tree.item(item)['text']
            if '..' not in text:  # 상위 폴더는 제외
                all_items.append(item)
        
        # 선택되지 않은 항목만 선택
        new_selection = [item for item in all_items if item not in currently_selected]
        tree.selection_set(new_selection)
        
        self.refresh_panel(self.active_panel)
    
    def compress_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "압축할 파일을 선택해주세요.")
            return
        
        # 압축 파일명 입력
        archive_name = simpledialog.askstring("압축하기", 
            "압축 파일 이름을 입력하세요 (확장자 제외):",
            initialvalue="archive")
        if not archive_name:
            return
        
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        archive_path = os.path.join(path, f"{archive_name}.zip")
        
        # 이미 존재하는 경우 확인
        if os.path.exists(archive_path):
            response = messagebox.askyesno("확인", 
                f"'{archive_name}.zip' 파일이 이미 존재합니다.\n덮어쓰시겠습니까?")
            if not response:
                return
        
        try:
            import zipfile
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    if os.path.isfile(file_path):
                        # 파일인 경우
                        zipf.write(file_path, os.path.basename(file_path))
                    elif os.path.isdir(file_path):
                        # 폴더인 경우 재귀적으로 추가
                        for root, dirs, files_in_dir in os.walk(file_path):
                            for file in files_in_dir:
                                file_full_path = os.path.join(root, file)
                                # 압축 파일 내에서의 경로
                                arcname = os.path.join(
                                    os.path.basename(file_path),
                                    os.path.relpath(file_full_path, file_path)
                                )
                                zipf.write(file_full_path, arcname)
            
            self.statusbar_label.config(text=f"'{archive_name}.zip' 압축 완료")
            self.refresh_panels()
            messagebox.showinfo("완료", f"'{archive_name}.zip' 파일이 생성되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"압축 실패: {str(e)}")


    # 4. 압축 풀기 - 완전한 버전
    def extract_files(self):
        files = self.get_selected_files()
        if not files or len(files) > 1:
            messagebox.showwarning("경고", "압축 파일을 하나만 선택해주세요.")
            return
        
        archive_path = files[0]
        ext = os.path.splitext(archive_path)[1].lower()
        
        if ext not in ['.zip']:
            messagebox.showwarning("경고", "현재 ZIP 파일만 지원됩니다.")
            return
        
        # 압축 해제 경로 설정
        extract_dir = os.path.join(
            os.path.dirname(archive_path), 
            os.path.splitext(os.path.basename(archive_path))[0]
        )
        
        # 이미 존재하는 경우 확인
        if os.path.exists(extract_dir):
            response = messagebox.askyesno("확인", 
                f"'{os.path.basename(extract_dir)}' 폴더가 이미 존재합니다.\n계속하시겠습니까?")
            if not response:
                return
        
        try:
            import zipfile
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                # 전체 파일 수 확인
                total_files = len(zipf.namelist())
                
                # 진행 상황 표시
                self.statusbar_label.config(text=f"압축 해제 중... (총 {total_files}개 파일)")
                self.root.update()
                
                # 압축 해제
                zipf.extractall(extract_dir)
            
            self.statusbar_label.config(text=f"압축 해제 완료: {extract_dir}")
            self.refresh_panels()
            messagebox.showinfo("완료", f"'{extract_dir}'에 압축이 해제되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"압축 해제 실패: {str(e)}")

    
    def open_terminal(self):
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        try:
            if platform.system() == 'Windows':
                # Windows에서 cmd 열기
                subprocess.Popen('start cmd', shell=True, cwd=path)
            elif platform.system() == 'Darwin':  # macOS
                # macOS에서 터미널 열기
                script = f'''
                tell application "Terminal"
                    do script "cd '{path}'"
                    activate
                end tell
                '''
                subprocess.Popen(['osascript', '-e', script])
            else:  # Linux
                # Linux에서 터미널 열기
                terminals = [
                    ('gnome-terminal', ['gnome-terminal', '--working-directory', path]),
                    ('konsole', ['konsole', '--workdir', path]),
                    ('xfce4-terminal', ['xfce4-terminal', '--working-directory', path]),
                    ('xterm', ['xterm', '-e', f'cd "{path}" && bash'])
                ]
                
                opened = False
                for term_name, cmd in terminals:
                    try:
                        subprocess.Popen(cmd)
                        opened = True
                        break
                    except:
                        continue
                
                if not opened:
                    messagebox.showerror("오류", "사용 가능한 터미널을 찾을 수 없습니다.")
                    return
            
            self.statusbar_label.config(text=f"터미널 열기: {path}")
        except Exception as e:
            messagebox.showerror("오류", f"터미널을 열 수 없습니다: {str(e)}")

def main():
    root = tk.Tk()
    app = TotalCommanderGUI(root)
    
    # F5, F6 키 바인딩 (붙여넣기)
    root.bind('<F5>', lambda e: app.paste_files('copy') if app.clipboard and app.clipboard_mode == 'copy' else app.copy_files())
    root.bind('<F6>', lambda e: app.paste_files('move') if app.clipboard and app.clipboard_mode == 'move' else app.move_files())
    
    root.mainloop()

if __name__ == "__main__":
    main()
