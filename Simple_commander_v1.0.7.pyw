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
        self.root.title("Simple Commander v1.06")
        self.root.geometry("1400x800")

        # 테마 정의 및 상태 초기화
        self.themes = {
            '라이트': {
                'main_bg': '#f0f0f0',
                'alt_bg': '#ffffff',
                'toolbar_bg': '#e9edf2',
                'toolbar_fg': '#2d3748',
                'accent': '#0078d7',
                'accent_fg': '#ffffff',
                'border': '#cbd2d9',
                'status_bg': '#e8e8e8',
                'status_fg': '#2d3748',
                'tree_fg': '#333333',
                'tree_bg': '#ffffff',
                'tree_head_bg': '#edf2f7',
                'tree_head_fg': '#2d3748',
                'tree_sel_bg': '#3182ce',
                'tree_sel_fg': '#ffffff'
            },
            '다크': {
                'main_bg': '#1f2933',
                'alt_bg': '#323f4b',
                'toolbar_bg': '#27323f',
                'toolbar_fg': '#f5f7fa',
                'accent': '#5aa9fa',
                'accent_fg': '#1d2733',
                'border': '#52606d',
                'status_bg': '#27323f',
                'status_fg': '#f5f7fa',
                'tree_fg': '#f5f7fa',
                'tree_bg': '#323f4b',
                'tree_head_bg': '#364350',
                'tree_head_fg': '#f5f7fa',
                'tree_sel_bg': '#5aa9fa',
                'tree_sel_fg': '#1d2733'
            }
        }
        self.current_theme = tk.StringVar(value='라이트')
        self.theme = self.themes[self.current_theme.get()]
        self.current_theme.trace_add('write', lambda *_: self.apply_theme())
        self.themable_widgets = []
        self.icon_tokens = ['📁', '🖼️', '🎵', '🎬', '📦', '📄', '💻', '📃', '📕', '📊', '📽️']

        # 전역 스타일 설정 (먼저 설정)
        self.setup_styles()
        self.apply_theme()
        
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
        self.setup_shortcuts()
        self.refresh_panels()
        
    def setup_styles(self):
        """전역 스타일 설정"""
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass

    def register_widget(self, widget, **option_map):
        self.themable_widgets.append((widget, option_map))
        self._apply_widget_theme(widget, option_map)

    def _apply_widget_theme(self, widget, option_map):
        palette = self.theme
        options = {}
        for option, key in option_map.items():
            if key is None:
                continue
            value = palette.get(key, key)
            options[option] = value
        if options:
            try:
                widget.configure(**options)
            except tk.TclError:
                # 일부 ttk 위젯은 직접 색상 지정이 제한된다.
                pass

    def apply_theme(self, *_):
        theme_name = self.current_theme.get()
        self.theme = self.themes.get(theme_name, self.themes['라이트'])
        palette = self.theme

        self.root.configure(bg=palette['main_bg'])

        # ttk 스타일 업데이트
        self.style.configure('Treeview',
                             background=palette['tree_bg'],
                             foreground=palette['tree_fg'],
                             fieldbackground=palette['tree_bg'],
                             borderwidth=1,
                             relief='solid',
                             rowheight=28)
        self.style.configure('Treeview.Heading',
                             background=palette['tree_head_bg'],
                             foreground=palette['tree_head_fg'],
                             borderwidth=1,
                             relief='raised',
                             font=('Arial', 9, 'bold'))
        self.style.map('Treeview',
                       background=[('selected', palette['tree_sel_bg'])],
                       foreground=[('selected', palette['tree_sel_fg'])])

        self.style.configure('Vertical.TScrollbar',
                             background=palette['alt_bg'],
                             troughcolor=palette['main_bg'],
                             borderwidth=1,
                             arrowcolor=palette['toolbar_fg'])
        self.style.configure('TCombobox',
                             fieldbackground=palette['alt_bg'],
                             background=palette['alt_bg'],
                             foreground=palette['toolbar_fg'])
        self.style.map('TCombobox',
                        fieldbackground=[('readonly', palette['alt_bg'])],
                        foreground=[('readonly', palette['toolbar_fg'])])

        # 등록된 위젯 색상 갱신
        for widget, option_map in self.themable_widgets:
            self._apply_widget_theme(widget, option_map)

        # Treeview 태그 색상 갱신
        panel_pairs = [
            (getattr(self, 'left_tree', None), getattr(self, 'left_status', None)),
            (getattr(self, 'right_tree', None), getattr(self, 'right_status', None))
        ]
        for tree, status_attr in panel_pairs:
            if tree is not None:
                try:
                    tree.tag_configure('file', foreground=palette['tree_fg'], background=palette['tree_bg'])
                    tree.tag_configure('dir', foreground=palette['tree_fg'], background=palette['tree_bg'])
                    tree.tag_configure('parent', foreground=palette['tree_fg'], background=palette['tree_bg'])
                    if hasattr(tree, 'context_menu'):
                        tree.context_menu.configure(bg=palette['alt_bg'], fg=palette['toolbar_fg'],
                                                     activebackground=palette['accent'],
                                                     activeforeground=palette['accent_fg'])
                except tk.TclError:
                    pass
            if status_attr is not None:
                self._apply_widget_theme(status_attr, {'bg': 'status_bg', 'fg': 'status_fg'})

        if hasattr(self, 'statusbar_label'):
            self._apply_widget_theme(self.statusbar_label, {'bg': 'status_bg', 'fg': 'status_fg'})
    
    def create_widgets(self):
        palette = self.theme

        # 메뉴바
        self.create_menubar()
        
        # 상단 툴바
        toolbar = tk.Frame(self.root, height=50, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(fill=tk.X, padx=0, pady=0)
        self.register_widget(toolbar, bg='toolbar_bg')
        self.toolbar = toolbar
        
        # 툴바 버튼들
        btn_frame = tk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT, padx=10, pady=5)
        self.register_widget(btn_frame, bg='toolbar_bg')
        
        toolbar_buttons = [
            ("↻", self.refresh_panels, "새로고침 (F5)"),
            ("🏠", self.go_home, "홈"),
            ("⬆", self.go_up, "상위 폴더"),
            ("←", lambda: self.navigate_history("back"), "뒤로"),
            ("→", lambda: self.navigate_history("forward"), "앞으로"),
        ]
        
        for text, command, tooltip in toolbar_buttons:
            btn = tk.Button(btn_frame, text=text, command=command,
                            bg=palette['alt_bg'], fg=palette['toolbar_fg'], relief=tk.RAISED,
                            font=('Arial', 12), width=3, height=1,
                            borderwidth=1, cursor="hand2",
                            activebackground=palette['accent'],
                            activeforeground=palette['accent_fg'])
            btn.pack(side=tk.LEFT, padx=2)
            self.register_widget(btn, bg='alt_bg', fg='toolbar_fg',
                                  activebackground='accent', activeforeground='accent_fg')
            self.create_tooltip(btn, tooltip)
        
        # 구분선
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 뷰 옵션
        view_frame = tk.Frame(toolbar)
        view_frame.pack(side=tk.LEFT, padx=5)
        self.register_widget(view_frame, bg='toolbar_bg')
        
        label_view = tk.Label(view_frame, text="보기:")
        label_view.pack(side=tk.LEFT, padx=5)
        self.register_widget(label_view, bg='toolbar_bg', fg='toolbar_fg')

        hidden_toggle = tk.Checkbutton(view_frame, text="숨김 파일", variable=self.view_hidden,
                                       command=self.refresh_panels)
        hidden_toggle.configure(bg=palette['toolbar_bg'], fg=palette['toolbar_fg'],
                                activebackground=palette['toolbar_bg'],
                                selectcolor=palette['toolbar_bg'])
        hidden_toggle.pack(side=tk.LEFT)
        self.register_widget(hidden_toggle, bg='toolbar_bg', fg='toolbar_fg', selectcolor='toolbar_bg')

        theme_label = tk.Label(view_frame, text="테마:")
        theme_label.pack(side=tk.LEFT, padx=(15, 5))
        self.register_widget(theme_label, bg='toolbar_bg', fg='toolbar_fg')

        self.theme_selector = ttk.Combobox(view_frame, values=list(self.themes.keys()),
                                           state='readonly', width=8, textvariable=self.current_theme)
        self.theme_selector.pack(side=tk.LEFT)
        self.theme_selector.set(self.current_theme.get())
        self.theme_selector.bind('<<ComboboxSelected>>', lambda _e: self.current_theme.set(self.theme_selector.get()))
        
        # 검색 박스
        search_frame = tk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT, padx=10)
        self.register_widget(search_frame, bg='toolbar_bg')

        search_icon = tk.Label(search_frame, text="🔍", font=('Arial', 12))
        search_icon.pack(side=tk.LEFT)
        self.register_widget(search_icon, bg='toolbar_bg', fg='toolbar_fg')

        self.search_entry = tk.Entry(search_frame, width=25,
                                     relief=tk.SOLID, borderwidth=1)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.register_widget(self.search_entry, bg='alt_bg', fg='toolbar_fg', insertbackground='toolbar_fg')
        self.search_entry.bind('<Return>', self.search_files)
        search_btn = tk.Button(search_frame, text="검색", command=self.search_files,
                               bg=palette['accent'], fg=palette['accent_fg'], relief=tk.RAISED,
                               borderwidth=1, cursor="hand2",
                               activebackground=palette['accent'], activeforeground=palette['accent_fg'])
        search_btn.pack(side=tk.LEFT)
        self.register_widget(search_btn, bg='accent', fg='accent_fg',
                              activebackground='accent', activeforeground='accent_fg')

        clear_btn = tk.Button(search_frame, text="초기화", command=self.clear_search,
                              bg=palette['alt_bg'], fg=palette['toolbar_fg'], relief=tk.RAISED,
                              borderwidth=1, cursor='hand2',
                              activebackground=palette['accent'], activeforeground=palette['accent_fg'])
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.register_widget(clear_btn, bg='alt_bg', fg='toolbar_fg',
                              activebackground='accent', activeforeground='accent_fg')
        
        # 메인 패널 컨테이너
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.register_widget(main_container, bg='main_bg')
        
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
        edit_menu.add_separator()
        edit_menu.add_command(label="경로 복사 (Ctrl+Shift+C)", command=self.copy_path_to_clipboard)
        edit_menu.add_command(label="탐색기로 열기", command=self.open_in_explorer)
        
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
        palette = self.theme
        panel = tk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        self.register_widget(panel, bg='main_bg')
        
        # 경로 입력
        path_frame = tk.Frame(panel, relief=tk.RAISED, borderwidth=1)
        path_frame.pack(fill=tk.X, pady=(0, 2))
        self.register_widget(path_frame, bg='toolbar_bg')
        
        path_icon = tk.Label(path_frame, text="📂", font=('Arial', 11))
        path_icon.pack(side=tk.LEFT, padx=5)
        self.register_widget(path_icon, bg='toolbar_bg', fg='toolbar_fg')
        
        path_entry = tk.Entry(path_frame, textvariable=path_var,
                              relief=tk.SOLID, borderwidth=1,
                              font=('Arial', 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        path_entry.bind('<Return>', lambda e: self.change_directory(side))
        self.register_widget(path_entry, bg='alt_bg', fg='toolbar_fg', insertbackground='toolbar_fg')
        
        # 드라이브 선택 버튼 (Windows)
        if platform.system() == 'Windows':
            drive_btn = tk.Button(path_frame, text="💾", command=lambda: self.select_drive(side),
                                  relief=tk.RAISED, borderwidth=1, cursor="hand2",
                                  bg=palette['alt_bg'], fg=palette['toolbar_fg'],
                                  activebackground=palette['accent'], activeforeground=palette['accent_fg'])
            drive_btn.pack(side=tk.RIGHT, padx=5)
            self.register_widget(drive_btn, bg='alt_bg', fg='toolbar_fg',
                                  activebackground='accent', activeforeground='accent_fg')
        
        # 파일 리스트 (Treeview)
        tree_frame = tk.Frame(panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.register_widget(tree_frame, bg='tree_bg')
        
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
        tree.tag_configure('file', foreground=palette['tree_fg'], background=palette['tree_bg'])
        tree.tag_configure('dir', foreground=palette['tree_fg'], background=palette['tree_bg'])
        tree.tag_configure('parent', foreground=palette['tree_fg'], background=palette['tree_bg'])
        
        # 이벤트 바인딩
        tree.bind('<FocusIn>', lambda e: self.on_panel_focus(side))
        tree.bind('<Double-Button-1>', lambda e: self.on_double_click(side))
        tree.bind('<Return>', lambda e: self.on_double_click(side))
        tree.bind('<Control-a>', lambda e: self.select_all())
        tree.bind('<Control-c>', lambda e: self.copy_files())
        tree.bind('<Control-x>', lambda e: self.move_files())
        tree.bind('<Control-v>', lambda e: self.paste_files())
        tree.bind('<Delete>', lambda e: self.delete_files())
        tree.bind('<space>', lambda e: self.toggle_selection(side))
        tree.bind('<<TreeviewSelect>>', lambda e: self.on_selection_change(side))
        
        # 우클릭 메뉴
        menu = tk.Menu(tree, tearoff=0,
                       bg=palette['alt_bg'], fg=palette['toolbar_fg'],
                       activebackground=palette['accent'], activeforeground=palette['accent_fg'],
                       borderwidth=1, relief=tk.RAISED)
        menu.add_command(label="열기", command=lambda: self.on_double_click(side))
        menu.add_separator()
        menu.add_command(label="복사 (F5)", command=self.copy_files)
        menu.add_command(label="이동 (F6)", command=self.move_files)
        menu.add_command(label="삭제 (F8)", command=self.delete_files)
        menu.add_separator()
        menu.add_command(label="이름 바꾸기", command=self.rename_file)
        menu.add_command(label="속성", command=self.show_properties)
        menu.add_separator()
        menu.add_command(label="경로 복사", command=lambda: self.copy_path_to_clipboard(side))
        menu.add_command(label="탐색기에서 열기", command=lambda: self.open_in_explorer(side))
        
        tree.bind('<Button-3>', lambda e: self.show_context_menu(e, menu, side))
        tree.context_menu = menu
        
        # 상태 표시
        status = tk.Label(panel, text="", 
                         anchor=tk.W, padx=5, pady=3, relief=tk.SUNKEN, borderwidth=1,
                         font=('Arial', 9))
        status.pack(fill=tk.X)
        self.register_widget(status, bg='status_bg', fg='status_fg')
        
        # 패널 정보 저장
        if side == "left":
            self.left_tree = tree
            self.left_status = status
            self.left_path_entry = path_entry
        else:
            self.right_tree = tree
            self.right_status = status
            self.right_path_entry = path_entry
        
        return panel
    
    def create_function_buttons(self):
        button_frame = tk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        button_frame.pack(fill=tk.X, padx=0, pady=0)
        self.register_widget(button_frame, bg='toolbar_bg')
        
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
        statusbar = tk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.register_widget(statusbar, bg='status_bg')
        
        self.statusbar_label = tk.Label(statusbar, text="준비됨", 
                                        anchor=tk.W, padx=10, pady=3,
                                        font=('Arial', 9))
        self.statusbar_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.register_widget(self.statusbar_label, bg='status_bg', fg='status_fg')

    def setup_shortcuts(self):
        self.root.bind('<Control-f>', self.focus_search)
        self.root.bind('<Control-l>', self.focus_path_entry)
        self.root.bind('<F2>', lambda e: self.rename_file())
        self.root.bind('<Control-Shift-C>', lambda e: (self.copy_path_to_clipboard(), "break")[1])
    
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
        tree, path, status = self._get_panel(side)
        
        # 현재 선택 상태 저장
        current_selection = tree.selection()
        selected_items = []
        for item in current_selection:
            item_text = tree.item(item)['text']
            selected_items.append(self._strip_icon_prefix(item_text))
        
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
                if item in selected_items:
                    new_selection.append(iid)
            
            # 선택 복원
            if new_selection:
                tree.selection_set(new_selection)
            
            # 상태 업데이트
            self._update_panel_status(side, total_items=len(items))
            self.statusbar_label.config(text=f"현재 위치: {path}")
            
        except Exception as e:
            messagebox.showerror("오류", f"경로를 열 수 없습니다: {str(e)}")

    def _get_panel(self, side):
        if side == "left":
            return self.left_tree, self.left_path.get(), self.left_status
        return self.right_tree, self.right_path.get(), self.right_status

    def _strip_icon_prefix(self, text):
        for token in self.icon_tokens:
            prefix = f"{token} "
            if text.startswith(prefix):
                return text[len(prefix):]
        return text

    def _update_panel_status(self, side, total_items=None):
        tree, path, status = self._get_panel(side)
        if tree is None or status is None:
            return

        if total_items is None:
            total_items = len([iid for iid in tree.get_children()
                               if self._strip_icon_prefix(tree.item(iid)['text']) != '..'])

        selection = [iid for iid in tree.selection()
                     if self._strip_icon_prefix(tree.item(iid)['text']) != '..']
        names = [self._strip_icon_prefix(tree.item(iid)['text']) for iid in selection]

        file_count = 0
        folder_count = 0
        total_size = 0
        for name in names:
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                folder_count += 1
            else:
                file_count += 1
                try:
                    total_size += os.path.getsize(full_path)
                except Exception:
                    pass

        selection_count = len(names)
        if selection_count > 0:
            size_text = f", 크기 {self.format_size(total_size)}" if file_count > 0 else ""
            status.config(
                text=(f"{selection_count}개 선택됨 (파일 {file_count}개, 폴더 {folder_count}개{size_text})"
                      f" / 총 {total_items}개 항목")
            )
        else:
            status.config(text=f"총 {total_items}개 항목")
    
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
        self._update_panel_status(side)
    
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

    def focus_path_entry(self, event=None):
        entry = self.left_path_entry if self.active_panel == "left" else getattr(self, 'right_path_entry', None)
        if entry:
            try:
                entry.focus_set()
                entry.select_range(0, tk.END)
            except tk.TclError:
                pass
        return "break"
    
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

    
    def get_selected_files(self, side=None):
        target_side = side or self.active_panel
        tree, path, _ = self._get_panel(target_side)
        if tree is None:
            return []

        files = []
        for item in tree.selection():
            text = self._strip_icon_prefix(tree.item(item)['text'])
            if text and text != '..':
                files.append(os.path.join(path, text))
        return files

    def copy_path_to_clipboard(self, side=None):
        files = self.get_selected_files(side)
        if not files:
            _, current_path, _ = self._get_panel(side or self.active_panel)
            files = [current_path]

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(files))
            if hasattr(self, 'statusbar_label'):
                self.statusbar_label.config(text=f"경로 복사 완료: {len(files)}개 항목")
        except tk.TclError:
            messagebox.showerror("오류", "클립보드에 접근할 수 없습니다.")

    def open_in_explorer(self, side=None):
        files = self.get_selected_files(side)
        _, current_path, _ = self._get_panel(side or self.active_panel)
        target = files[0] if files else current_path
        target = os.path.abspath(target)

        try:
            system = platform.system()
            if system == 'Windows':
                norm = os.path.normpath(target)
                if os.path.isfile(norm):
                    subprocess.Popen(['explorer', '/select,', norm])
                else:
                    subprocess.Popen(['explorer', norm])
            elif system == 'Darwin':
                if os.path.isfile(target):
                    subprocess.Popen(['open', '-R', target])
                else:
                    subprocess.Popen(['open', target])
            else:
                folder = target if os.path.isdir(target) else os.path.dirname(target)
                opener = shutil.which('xdg-open')
                if not opener:
                    raise RuntimeError('xdg-open을 찾을 수 없습니다.')
                subprocess.Popen([opener, folder])

            if hasattr(self, 'statusbar_label'):
                self.statusbar_label.config(text=f"탐색기로 열기: {os.path.basename(target) or target}")
        except Exception as e:
            messagebox.showerror("오류", f"탐색기를 열 수 없습니다: {str(e)}")
    
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
        if not files:
            messagebox.showwarning("경고", "복사할 파일을 선택해주세요.")
            return

        # 대상 경로 설정 (반대쪽 패널)
        if self.active_panel == "left":
            dest_path = self.right_path.get()
        else:
            dest_path = self.left_path.get()

        # 대상 경로가 유효한지 확인
        if not os.path.isdir(dest_path):
            messagebox.showerror("오류", "대상 경로가 유효하지 않습니다.")
            return

        try:
            total = len(files)
            success_count = 0
            
            for src_path in files:
                filename = os.path.basename(src_path)
                dest_file = os.path.join(dest_path, filename)
                
                # 파일이 이미 존재하는지 확인
                if os.path.exists(dest_file):
                    result = messagebox.askyesnocancel(
                        "파일 존재",
                        f"'{filename}' 파일이 이미 존재합니다.\n덮어쓰시겠습니까?\n\n예: 덮어쓰기\n아니오: 새 이름으로 저장\n취소: 작업 중단"
                    )
                    
                    if result is None:  # 취소
                        break
                    elif not result:  # 아니오 (새 이름으로 저장)
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while True:
                            new_name = f"{base}_복사본{counter}{ext}"
                            new_dest = os.path.join(dest_path, new_name)
                            if not os.path.exists(new_dest):
                                dest_file = new_dest
                                break
                            counter += 1
                
                try:
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_file)
                    else:
                        shutil.copy2(src_path, dest_file)
                    
                    success_count += 1
                    
                except Exception as e:
                    messagebox.showerror("오류", f"'{filename}' 복사 중 오류: {str(e)}")
                    continue
            
            # 결과 메시지
            if success_count == total:
                message = f"모든 항목이 성공적으로 복사되었습니다."
            else:
                message = f"{success_count}/{total}개 항목이 복사되었습니다."
            
            messagebox.showinfo("복사 완료", message)
            
            # 패널 새로고침
            self.refresh_panels()
            self.statusbar_label.config(text=f"복사 완료: {success_count}개 항목")
            
        except Exception as e:
            messagebox.showerror("오류", f"복사 중 오류 발생: {str(e)}")

    def move_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "이동할 파일을 선택해주세요.")
            return

        # 대상 경로 설정 (반대쪽 패널)
        if self.active_panel == "left":
            dest_path = self.right_path.get()
        else:
            dest_path = self.left_path.get()

        # 대상 경로가 유효한지 확인
        if not os.path.isdir(dest_path):
            messagebox.showerror("오류", "대상 경로가 유효하지 않습니다.")
            return

        # 같은 경로로 이동하려는 경우 확인
        src_dir = os.path.dirname(files[0]) if files else ""
        if src_dir == dest_path:
            messagebox.showwarning("경고", "같은 폴더로는 이동할 수 없습니다.")
            return

        try:
            total = len(files)
            success_count = 0
            
            for src_path in files:
                filename = os.path.basename(src_path)
                dest_file = os.path.join(dest_path, filename)
                
                # 파일이 이미 존재하는지 확인
                if os.path.exists(dest_file):
                    result = messagebox.askyesnocancel(
                        "파일 존재",
                        f"'{filename}' 파일이 이미 존재합니다.\n덮어쓰시겠습니까?\n\n예: 덮어쓰기\n아니오: 새 이름으로 저장\n취소: 작업 중단"
                    )
                    
                    if result is None:  # 취소
                        break
                    elif not result:  # 아니오 (새 이름으로 저장)
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while True:
                            new_name = f"{base}_이동{counter}{ext}"
                            new_dest = os.path.join(dest_path, new_name)
                            if not os.path.exists(new_dest):
                                dest_file = new_dest
                                break
                            counter += 1
                
                try:
                    shutil.move(src_path, dest_file)
                    success_count += 1
                    
                except Exception as e:
                    messagebox.showerror("오류", f"'{filename}' 이동 중 오류: {str(e)}")
                    continue
            
            # 결과 메시지
            if success_count == total:
                message = f"모든 항목이 성공적으로 이동되었습니다."
            else:
                message = f"{success_count}/{total}개 항목이 이동되었습니다."
            
            messagebox.showinfo("이동 완료", message)
            
            # 패널 새로고침
            self.refresh_panels()
            self.statusbar_label.config(text=f"이동 완료: {success_count}개 항목")
            
        except Exception as e:
            messagebox.showerror("오류", f"이동 중 오류 발생: {str(e)}")

    def paste_files(self):
        """기존 클립보드 방식의 붙여넣기 (옵션으로 유지)"""
        if not self.clipboard:
            messagebox.showwarning("경고", "붙여넣을 항목이 없습니다.")
            return
        
        # 대상 경로 설정
        if self.clipboard_origin == 'left':
            dest_path = self.right_path.get()
        elif self.clipboard_origin == 'right':
            dest_path = self.left_path.get()
        else:
            # fallback: 현재 활성 패널
            dest_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        # 대상 경로가 유효한지 확인
        if not os.path.isdir(dest_path):
            messagebox.showerror("오류", "대상 경로가 유효하지 않습니다.")
            return

        try:
            total = len(self.clipboard)
            success_count = 0
            
            for src_path in self.clipboard:
                filename = os.path.basename(src_path)
                dest_file = os.path.join(dest_path, filename)
                
                # 파일이 이미 존재하는지 확인
                if os.path.exists(dest_file):
                    result = messagebox.askyesnocancel(
                        "파일 존재",
                        f"'{filename}' 파일이 이미 존재합니다.\n덮어쓰시겠습니까?\n\n예: 덮어쓰기\n아니오: 새 이름으로 저장\n취소: 작업 중단"
                    )
                    
                    if result is None:  # 취소
                        break
                    elif not result:  # 아니오 (새 이름으로 저장)
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while True:
                            new_name = f"{base}_붙여넣기{counter}{ext}"
                            new_dest = os.path.join(dest_path, new_name)
                            if not os.path.exists(new_dest):
                                dest_file = new_dest
                                break
                            counter += 1
                
                try:
                    if self.clipboard_mode == 'copy':
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dest_file)
                        else:
                            shutil.copy2(src_path, dest_file)
                    else:  # move
                        shutil.move(src_path, dest_file)
                    
                    success_count += 1
                    
                except Exception as e:
                    messagebox.showerror("오류", f"'{filename}' 처리 중 오류: {str(e)}")
                    continue
            
            # 결과 메시지
            if self.clipboard_mode == 'copy':
                action = "복사"
            else:
                action = "이동"
            
            if success_count == total:
                message = f"모든 항목이 성공적으로 {action}되었습니다."
            else:
                message = f"{success_count}/{total}개 항목이 {action}되었습니다."
            
            messagebox.showinfo("완료", message)
            
            # 이동 모드인 경우 클립보드 비우기
            if self.clipboard_mode == 'move':
                self.clipboard = []
                self.clipboard_mode = None
                self.clipboard_origin = None
            
            # 패널 새로고침
            self.refresh_panels()
            self.statusbar_label.config(text=f"{action} 완료: {success_count}개 항목")
            
        except Exception as e:
            messagebox.showerror("오류", f"붙여넣기 중 오류 발생: {str(e)}")

    def delete_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "삭제할 파일을 선택해주세요.")
            return
        
        file_list = "\n".join([f"• {os.path.basename(f)}" for f in files])
        result = messagebox.askyesno(
            "삭제 확인",
            f"다음 항목들을 삭제하시겠습니까?\n\n{file_list}\n\n이 작업은 되돌릴 수 없습니다."
        )
        
        if not result:
            return
        
        success_count = 0
        total = len(files)
        
        for file_path in files:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                success_count += 1
            except Exception as e:
                messagebox.showerror("오류", f"'{os.path.basename(file_path)}' 삭제 중 오류: {str(e)}")
        
        if success_count == total:
            messagebox.showinfo("완료", "모든 항목이 삭제되었습니다.")
        else:
            messagebox.showinfo("완료", f"{success_count}/{total}개 항목이 삭제되었습니다.")
        
        self.refresh_panels()
        self.statusbar_label.config(text=f"삭제 완료: {success_count}개 항목")

    def new_folder(self):
        current_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        name = simpledialog.askstring("새 폴더", "폴더 이름을 입력하세요:")
        if not name:
            return
        
        new_path = os.path.join(current_path, name)
        
        try:
            os.makedirs(new_path, exist_ok=False)
            self.refresh_panel(self.active_panel)
            self.statusbar_label.config(text=f"폴더 생성됨: {name}")
        except FileExistsError:
            messagebox.showerror("오류", "같은 이름의 폴더가 이미 존재합니다.")
        except Exception as e:
            messagebox.showerror("오류", f"폴더를 생성할 수 없습니다: {str(e)}")

    def new_file(self):
        current_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        name = simpledialog.askstring("새 파일", "파일 이름을 입력하세요:")
        if not name:
            return
        
        new_path = os.path.join(current_path, name)
        
        try:
            with open(new_path, 'w', encoding='utf-8') as f:
                pass
            self.refresh_panel(self.active_panel)
            self.statusbar_label.config(text=f"파일 생성됨: {name}")
        except Exception as e:
            messagebox.showerror("오류", f"파일을 생성할 수 없습니다: {str(e)}")

    def rename_file(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "이름을 바꿀 파일을 선택해주세요.")
            return
        
        if len(files) > 1:
            messagebox.showwarning("경고", "한 번에 하나의 파일만 이름을 바꿀 수 있습니다.")
            return
        
        old_path = files[0]
        old_name = os.path.basename(old_path)
        directory = os.path.dirname(old_path)
        
        new_name = simpledialog.askstring("이름 바꾸기", "새 이름을 입력하세요:", initialvalue=old_name)
        if not new_name or new_name == old_name:
            return
        
        new_path = os.path.join(directory, new_name)
        
        try:
            os.rename(old_path, new_path)
            self.refresh_panels()
            self.statusbar_label.config(text=f"이름 변경: {old_name} → {new_name}")
        except Exception as e:
            messagebox.showerror("오류", f"이름을 바꿀 수 없습니다: {str(e)}")

    def show_properties(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "속성을 볼 파일을 선택해주세요.")
            return
        
        if len(files) > 1:
            # 여러 파일 속성
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for file_path in files:
                try:
                    if os.path.isdir(file_path):
                        dir_count += 1
                        # 폴더 크기 계산 (주의: 큰 폴더는 시간이 오래 걸릴 수 있음)
                        for dirpath, dirnames, filenames in os.walk(file_path):
                            for f in filenames:
                                fp = os.path.join(dirpath, f)
                                try:
                                    total_size += os.path.getsize(fp)
                                except:
                                    pass
                    else:
                        file_count += 1
                        total_size += os.path.getsize(file_path)
                except:
                    pass
            
            message = f"선택 항목: {len(files)}개\n"
            message += f"파일: {file_count}개\n"
            message += f"폴더: {dir_count}개\n"
            message += f"총 크기: {self.format_size(total_size)}\n"
            
            messagebox.showinfo("속성", message)
        else:
            # 단일 파일 속성
            file_path = files[0]
            try:
                stat = os.stat(file_path)
                name = os.path.basename(file_path)
                
                message = f"이름: {name}\n"
                message += f"경로: {file_path}\n"
                message += f"종류: {'폴더' if os.path.isdir(file_path) else '파일'}\n"
                
                if os.path.isfile(file_path):
                    message += f"크기: {self.format_size(stat.st_size)}\n"
                
                message += f"수정한 날짜: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
                message += f"만든 날짜: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n"
                message += f"접근한 날짜: {datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                messagebox.showinfo("속성", message)
            except Exception as e:
                messagebox.showerror("오류", f"속성을 가져올 수 없습니다: {str(e)}")

    def select_all(self):
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        items = [item for item in tree.get_children() if '..' not in tree.item(item)['text']]
        tree.selection_set(items)

    def invert_selection(self):
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        all_items = [item for item in tree.get_children() if '..' not in tree.item(item)['text']]
        current_selection = tree.selection()
        
        new_selection = [item for item in all_items if item not in current_selection]
        tree.selection_set(new_selection)

    def toggle_selection(self, side):
        tree = self.left_tree if side == "left" else self.right_tree
        selection = tree.selection()
        if selection:
            current_item = selection[0]
            if current_item in tree.selection():
                tree.selection_remove(current_item)
            else:
                tree.selection_add(current_item)

    def show_context_menu(self, event, menu, side):
        tree = self.left_tree if side == "left" else self.right_tree
        try:
            item = tree.identify_row(event.y)
            if item:
                tree.selection_set(item)
                self.on_panel_focus(side)
                menu.post(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def focus_search(self, event=None):
        if hasattr(self, 'search_entry') and self.search_entry:
            try:
                self.search_entry.focus_set()
                self.search_entry.select_range(0, tk.END)
            except tk.TclError:
                pass
        return "break"

    def clear_search(self):
        if hasattr(self, 'search_entry') and self.search_entry:
            self.search_entry.delete(0, tk.END)
        self.refresh_panel(self.active_panel)
        if hasattr(self, 'statusbar_label'):
            self.statusbar_label.config(text="검색 초기화")
        self.focus_search()

    def search_files(self, event=None):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("경고", "검색어를 입력해주세요.")
            return
        
        # 현재 활성 패널의 경로에서 검색
        search_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        results = []
        try:
            for root, dirs, files in os.walk(search_path):
                # 숨김 파일/폴더 제외
                if not self.view_hidden.get():
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]
                
                for name in dirs + files:
                    if query.lower() in name.lower():
                        full_path = os.path.join(root, name)
                        results.append(full_path)
                        
                        # 결과가 너무 많으면 중단
                        if len(results) >= 1000:
                            break
                
                if len(results) >= 1000:
                    break
        except Exception as e:
            messagebox.showerror("오류", f"검색 중 오류 발생: {str(e)}")
            return
        
        # 검색 결과 창 표시
        self.show_search_results(query, results, search_path)
        if hasattr(self, 'statusbar_label'):
            self.statusbar_label.config(text=f"검색: '{query}' 결과 {len(results)}개")

    def show_search_results(self, query, results, search_path):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"검색 결과: '{query}' ({len(results)}개 항목)")
        dialog.geometry("800x600")
        dialog.configure(bg="white")
        dialog.transient(self.root)
        
        # 결과 프레임
        frame = tk.Frame(dialog, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 결과 리스트
        listbox = tk.Listbox(frame, font=('Arial', 10), yscrollcommand=scrollbar.set)
        listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for result in results:
            # 검색 경로를 기준으로 상대 경로 표시
            relative_path = os.path.relpath(result, search_path)
            listbox.insert(tk.END, relative_path)
        
        # 더블클릭으로 파일 열기
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                file_path = results[selection[0]]
                self.view_file_at_path(file_path)
                dialog.destroy()
        
        listbox.bind('<Double-Button-1>', on_double_click)
        
        # 버튼 프레임
        button_frame = tk.Frame(dialog, bg="white")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="열기", command=lambda: on_double_click(None),
                 bg="#0078d7", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="취소", command=dialog.destroy,
                 bg="#666666", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def view_file_at_path(self, file_path):
        """특정 경로의 파일을 보기"""
        if os.path.isfile(file_path):
            try:
                if platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', file_path))
                elif platform.system() == 'Windows':
                    os.startfile(file_path)
                else:  # Linux
                    subprocess.call(('xdg-open', file_path))
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

    def compress_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "압축할 파일을 선택해주세요.")
            return
        
        # 압축 파일 이름 입력
        default_name = "압축파일.zip"
        archive_name = simpledialog.askstring("압축하기", "압축 파일 이름을 입력하세요:", 
                                             initialvalue=default_name)
        if not archive_name:
            return
        
        # 확장자 확인
        if not archive_name.lower().endswith(('.zip', '.tar', '.gz')):
            archive_name += '.zip'
        
        current_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        archive_path = os.path.join(current_path, archive_name)
        
        try:
            import zipfile
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    if os.path.isfile(file_path):
                        zipf.write(file_path, os.path.basename(file_path))
                    elif os.path.isdir(file_path):
                        for root, dirs, files_in_dir in os.walk(file_path):
                            for file in files_in_dir:
                                file_full_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_full_path, os.path.dirname(file_path))
                                zipf.write(file_full_path, arcname)
            
            messagebox.showinfo("완료", f"압축이 완료되었습니다: {archive_name}")
            self.refresh_panel(self.active_panel)
            self.statusbar_label.config(text=f"압축 완료: {archive_name}")
            
        except Exception as e:
            messagebox.showerror("오류", f"압축 중 오류 발생: {str(e)}")

    def extract_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "압축을 풀 파일을 선택해주세요.")
            return
        
        archive_path = files[0]
        supported_extensions = ('.zip', '.tar', '.gz', '.bz2', '.rar', '.7z')
        
        if not archive_path.lower().endswith(supported_extensions):
            messagebox.showwarning("경고", "지원하지 않는 압축 형식입니다.")
            return
        
        current_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        extract_path = current_path
        
        try:
            import zipfile
            import tarfile
            
            if archive_path.lower().endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_path)
            elif archive_path.lower().endswith(('.tar', '.gz', '.bz2')):
                with tarfile.open(archive_path, 'r:*') as tar:
                    tar.extractall(extract_path)
            else:
                messagebox.showwarning("경고", "이 형식의 압축 풀기는 아직 지원되지 않습니다.")
                return
            
            messagebox.showinfo("완료", "압축 풀기가 완료되었습니다.")
            self.refresh_panel(self.active_panel)
            self.statusbar_label.config(text="압축 풀기 완료")
            
        except Exception as e:
            messagebox.showerror("오류", f"압축 풀기 중 오류 발생: {str(e)}")

    def open_terminal(self):
        current_path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(['cmd.exe'], cwd=current_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', '-a', 'Terminal', current_path])
            else:  # Linux
                terminals = ['gnome-terminal', 'konsole', 'xterm', 'terminator']
                opened = False
                for term in terminals:
                    try:
                        subprocess.Popen([term, '--working-directory', current_path])
                        opened = True
                        break
                    except:
                        continue
                
                if not opened:
                    messagebox.showerror("오류", "사용 가능한 터미널을 찾을 수 없습니다.")
                    return
            
            self.statusbar_label.config(text=f"터미널 열기: {current_path}")
        except Exception as e:
            messagebox.showerror("오류", f"터미널을 열 수 없습니다: {str(e)}")

def main():
    root = tk.Tk()
    app = TotalCommanderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()