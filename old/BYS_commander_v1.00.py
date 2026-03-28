import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
        self.root.geometry("1200x700")
        self.root.configure(bg="#1a1a1a")
        
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
        
        self.create_widgets()
        self.refresh_panels()
    
    def setup_styles(self):
        """전역 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Treeview 스타일
        style.configure('Treeview', 
                       background='#1a1a1a', 
                       foreground='white',
                       fieldbackground='#1a1a1a', 
                       borderwidth=0,
                       rowheight=25)
        style.configure('Treeview.Heading', 
                       background='#2d2d2d', 
                       foreground='white',
                       borderwidth=1,
                       relief='flat')
        style.map('Treeview', 
                 background=[('selected', '#1e3a5f')],
                 foreground=[('selected', 'white')])
        
        # Scrollbar 스타일
        style.configure('Vertical.TScrollbar',
                       background='#2d2d2d',
                       troughcolor='#1a1a1a',
                       borderwidth=0,
                       arrowcolor='white')
        
    def create_widgets(self):
        # 상단 툴바
        toolbar = tk.Frame(self.root, bg="#2d2d2d", height=40)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="↻ 새로고침", bg="#404040", fg="white", 
                 command=self.refresh_panels, relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="🏠 홈", bg="#404040", fg="white", 
                 command=self.go_home, relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        
        # 검색 박스
        search_frame = tk.Frame(toolbar, bg="#1a1a1a")
        search_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(search_frame, text="🔍", bg="#1a1a1a", fg="white").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, bg="#1a1a1a", fg="white", width=30, 
                insertbackground="white")
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', self.search_files)
        
        # 메인 패널 컨테이너
        main_container = tk.Frame(self.root, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # 좌측 패널
        self.left_panel = self.create_panel(main_container, self.left_path, "left")
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        # 우측 패널
        self.right_panel = self.create_panel(main_container, self.right_path, "right")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        # 하단 기능 버튼
        self.create_function_buttons()
        
    def create_panel(self, parent, path_var, side):
        panel = tk.Frame(parent, bg="#1a1a1a")
        
        # 경로 입력
        path_frame = tk.Frame(panel, bg="#2d2d2d")
        path_frame.pack(fill=tk.X, pady=(0, 2))
        
        tk.Label(path_frame, text="💾", bg="#2d2d2d", fg="white").pack(side=tk.LEFT, padx=5)
        path_entry = tk.Entry(path_frame, textvariable=path_var, bg="#1a1a1a", 
                             fg="white", insertbackground="white")
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        path_entry.bind('<Return>', lambda e: self.refresh_panels())
        
        # 파일 리스트 (Treeview)
        tree_frame = tk.Frame(panel, bg="#1a1a1a")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ('size', 'date')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings',
                           yscrollcommand=scrollbar.set, selectmode='extended')
        
        tree.heading('#0', text='이름')
        tree.heading('size', text='크기')
        tree.heading('date', text='수정 날짜')
        
        tree.column('#0', width=300)
        tree.column('size', width=100)
        tree.column('date', width=150)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)
        
        # 이벤트 바인딩
        tree.bind('<Button-1>', lambda e: self.on_panel_click(side))
        tree.bind('<Double-Button-1>', lambda e: self.on_double_click(side))
        tree.bind('<Return>', lambda e: self.on_double_click(side))
        
        # 우클릭 메뉴
        menu = tk.Menu(tree, tearoff=0, bg="#2d2d2d", fg="white",
                      activebackground="#404040", activeforeground="white",
                      borderwidth=0)
        menu.add_command(label="열기", command=lambda: self.on_double_click(side))
        menu.add_separator()
        menu.add_command(label="복사 (F5)", command=self.copy_files)
        menu.add_command(label="이동 (F6)", command=self.move_files)
        menu.add_command(label="삭제 (F8)", command=self.delete_files)
        menu.add_separator()
        menu.add_command(label="이름 바꾸기", command=self.rename_file)
        menu.add_command(label="속성", command=self.show_properties)
        
        tree.bind('<Button-3>', lambda e: self.show_context_menu(e, menu, side))
        
        # 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', 
                       background='#1a1a1a', 
                       foreground='white',
                       fieldbackground='#1a1a1a', 
                       borderwidth=0,
                       rowheight=25)
        style.configure('Treeview.Heading', 
                       background='#2d2d2d', 
                       foreground='white',
                       borderwidth=1,
                       relief='flat')
        style.map('Treeview', 
                 background=[('selected', '#1e3a5f')],
                 foreground=[('selected', 'white')])
        
        # 상태 표시
        status = tk.Label(panel, text="", bg="#2d2d2d", fg="#888888", 
                         anchor=tk.W, padx=5, pady=2)
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
        button_frame = tk.Frame(self.root, bg="#2d2d2d")
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons = [
            ("F3 보기", self.view_file, "#404040"),
            ("F4 편집", self.edit_file, "#404040"),
            ("F5 복사", self.copy_files, "#404040"),
            ("F6 이동", self.move_files, "#404040"),
            ("F7 새폴더", self.new_folder, "#404040"),
            ("F8 삭제", self.delete_files, "#8b0000"),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, bg=color, fg="white",
                          command=command, relief=tk.FLAT, padx=15, pady=8)
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            
            # 키 바인딩
            key = text.split()[0].lower()
            self.root.bind(f'<{key.upper()}>', lambda e, c=command: c())
    
    def refresh_panels(self):
        self.refresh_panel("left")
        self.refresh_panel("right")
    
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
            
            # 상위 디렉토리 항목
            if os.path.dirname(path) != path:  # 루트가 아닐 때만
                tree.insert('', 'end', text='📁 ..', values=('', ''), tags=('parent',))
            
            # 파일 및 폴더 목록
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                try:
                    stat = os.stat(full_path)
                    size = self.format_size(stat.st_size) if os.path.isfile(full_path) else ''
                    date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    is_dir = os.path.isdir(full_path)
                    items.append((item, is_dir, size, date))
                except:
                    continue
            
            # 폴더 먼저, 이름순 정렬
            items.sort(key=lambda x: (not x[1], x[0].lower()))
            
            # 트리에 추가
            for item, is_dir, size, date in items:
                icon = '📁' if is_dir else self.get_file_icon(item)
                tree.insert('', 'end', text=f'{icon} {item}', 
                           values=(size, date), tags=('dir' if is_dir else 'file',))
            
            # 상태 업데이트
            selected_count = len(tree.selection())
            if selected_count > 0:
                status.config(text=f"{selected_count}개 선택됨 / 총 {len(items)}개 항목")
            else:
                status.config(text=f"{len(items)}개 항목")
            
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
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return '🖼️'
        elif ext in ['.mp3', '.wav', '.flac', '.m4a']:
            return '🎵'
        elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
            return '🎬'
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return '📦'
        elif ext in ['.txt', '.doc', '.docx', '.pdf']:
            return '📄'
        elif ext in ['.py', '.js', '.java', '.cpp', '.c']:
            return '💻'
        else:
            return '📃'
    
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
            # 파일 열기
            self.view_file()
    
    def get_selected_files(self):
        tree = self.left_tree if self.active_panel == "left" else self.right_tree
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        selection = tree.selection()
        files = []
        
        for item in selection:
            text = tree.item(item)['text']
            # 아이콘 제거
            for icon in ['📁', '🖼️', '🎵', '🎬', '📦', '📄', '💻', '📃']:
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
                if platform.system() == 'Windows':
                    os.startfile(file_path, 'edit')
                else:
                    # 텍스트 편집기로 열기
                    editors = ['nano', 'vim', 'gedit', 'kate', 'notepad']
                    for editor in editors:
                        try:
                            subprocess.Popen([editor, file_path])
                            break
                        except:
                            continue
            except Exception as e:
                messagebox.showerror("오류", f"파일을 편집할 수 없습니다: {str(e)}")
    
    def copy_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        self.clipboard = files
        self.clipboard_mode = 'copy'
        messagebox.showinfo("복사", f"{len(files)}개 항목이 클립보드에 복사되었습니다.\n반대쪽 패널에서 F5를 눌러 붙여넣기하세요.")
    
    def move_files(self):
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        self.clipboard = files
        self.clipboard_mode = 'move'
        messagebox.showinfo("이동", f"{len(files)}개 항목이 이동 대기 중입니다.\n반대쪽 패널에서 F6를 눌러 이동하세요.")
    
    def paste_files(self, mode):
        if not self.clipboard:
            messagebox.showwarning("경고", "복사/이동할 항목이 없습니다.")
            return
        
        # 대상 경로 (현재 활성 패널)
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
        
        # 클립보드 초기화 (이동의 경우)
        if mode == 'move':
            self.clipboard = []
            self.clipboard_mode = None
        
        self.refresh_panels()
        
        if success_count > 0:
            action = "복사" if mode == 'copy' else "이동"
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
            messagebox.showinfo("완료", f"{success_count}개 항목이 삭제되었습니다.")
    
    def new_folder(self):
        path = self.left_path.get() if self.active_panel == "left" else self.right_path.get()
        
        name = simpledialog.askstring("새 폴더", "폴더 이름을 입력하세요:")
        if not name:
            return
        
        new_path = os.path.join(path, name)
        
        try:
            os.makedirs(new_path)
            messagebox.showinfo("완료", f"'{name}' 폴더가 생성되었습니다.")
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
            messagebox.showinfo("완료", f"'{old_name}'이(가) '{new_name}'(으)로 변경되었습니다.")
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
            
            info = f"이름: {os.path.basename(file_path)}\n"
            info += f"경로: {file_path}\n"
            info += f"크기: {size}\n"
            info += f"수정 날짜: {modified}\n"
            info += f"타입: {'디렉토리' if os.path.isdir(file_path) else '파일'}"
            
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
    
    def go_home(self):
        home = str(Path.home())
        if self.active_panel == "left":
            self.left_path.set(home)
        else:
            self.right_path.set(home)
        self.refresh_panels()

def main():
    root = tk.Tk()
    app = TotalCommanderGUI(root)
    
    # F5, F6 키 바인딩 (붙여넣기)
    root.bind('<F5>', lambda e: app.paste_files('copy') if app.clipboard and app.clipboard_mode == 'copy' else app.copy_files())
    root.bind('<F6>', lambda e: app.paste_files('move') if app.clipboard and app.clipboard_mode == 'move' else app.move_files())
    
    root.mainloop()

if __name__ == "__main__":
    main()