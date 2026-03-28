# 1. 파일 보기 (F3) - 개선된 버전
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


# 2. 파일 편집 (F4) - 개선된 버전
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


# 3. 압축하기 - 완전한 버전
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


# 5. 터미널 열기 - 완전한 버전
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


# 6. 드라이브 선택 - 완전한 버전 (Windows 전용)
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


# 7. 검색 기능 - 개선된 버전
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


# 8. 새 파일 만들기 - 개선된 버전
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