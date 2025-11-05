# Contributing to Simple Commander

Simple Commander 프로젝트에 기여해 주셔서 감사합니다! 🎉

## 기여 방법

### 1. 버그 리포트

버그를 발견하셨나요? 다음 정보를 포함해서 Issue를 작성해주세요:

- **버그 설명**: 어떤 문제가 발생했나요?
- **재현 방법**: 어떻게 하면 버그가 발생하나요?
- **예상 동작**: 어떻게 동작해야 하나요?
- **실제 동작**: 실제로 어떻게 동작했나요?
- **환경 정보**:
  - OS: (예: Windows 11, macOS 14, Ubuntu 22.04)
  - Python 버전: (예: Python 3.11.5)
  - 스크린샷 (가능하다면)

### 2. 기능 제안

새로운 기능을 제안하고 싶으신가요?

- Issue를 열고 `[Feature Request]` 태그를 붙여주세요
- 어떤 기능이 필요한지 자세히 설명해주세요
- 왜 이 기능이 유용한지 설명해주세요
- 가능하다면 사용 예시를 포함해주세요

### 3. Pull Request

코드 기여를 환영합니다! 다음 단계를 따라주세요:

#### Step 1: Fork & Clone
```bash
# 1. GitHub에서 이 저장소를 Fork 합니다
# 2. Fork한 저장소를 클론합니다
git clone https://github.com/artofstock/Simple-Commander.git
cd Simple-Commander
```

#### Step 2: 브랜치 만들기
```bash
# 새로운 브랜치를 만듭니다
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/your-bug-fix
```

#### Step 3: 코드 작성

- 기존 코드 스타일을 유지해주세요
- 의미 있는 변수명과 함수명을 사용해주세요
- 필요한 경우 주석을 추가해주세요
- 가능하다면 테스트를 추가해주세요

#### Step 4: 커밋
```bash
git add .
git commit -m "feat: 새로운 기능 추가"
# 또는
git commit -m "fix: 버그 수정"
```

**커밋 메시지 컨벤션:**
- `feat:` - 새로운 기능
- `fix:` - 버그 수정
- `docs:` - 문서 수정
- `style:` - 코드 포맷팅 (기능 변경 없음)
- `refactor:` - 코드 리팩토링
- `test:` - 테스트 추가
- `chore:` - 빌드 작업, 패키지 매니저 설정 등

#### Step 5: Push & Pull Request
```bash
git push origin feature/your-feature-name
```

- GitHub에서 Pull Request를 생성합니다
- PR 설명에 변경 내용을 자세히 작성해주세요
- 관련된 Issue가 있다면 링크해주세요

## 코딩 스타일 가이드

### Python 코딩 스타일
```python
# 1. 함수명과 변수명: snake_case
def calculate_file_size(path):
    file_size = os.path.getsize(path)
    return file_size

# 2. 클래스명: PascalCase
class FileManager:
    pass

# 3. 상수: UPPER_CASE
MAX_FILE_SIZE = 1024 * 1024

# 4. 들여쓰기: 스페이스 4칸
def example_function():
    if True:
        print("Hello")

# 5. 주석은 명확하게
# 나쁜 예
x = x + 1  # x 증가

# 좋은 예
file_count = file_count + 1  # 처리된 파일 개수 증가
```

### 문서화
```python
def copy_files(self, source, destination):
    """
    파일을 복사합니다.
    
    Args:
        source (str): 원본 파일 경로
        destination (str): 대상 파일 경로
    
    Returns:
        bool: 성공 시 True, 실패 시 False
    
    Raises:
        FileNotFoundError: 원본 파일이 없을 때
    """
    pass
```

## 코드 리뷰 프로세스

1. PR을 제출하면 메인테이너가 리뷰합니다
2. 필요한 경우 수정을 요청할 수 있습니다
3. 모든 체크가 통과하면 merge됩니다

## 개발 환경 설정
```bash
# Python 가상환경 생성 (선택사항)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 의존성 설치 (현재는 표준 라이브러리만 사용)
# 추가 패키지가 필요한 경우 requirements.txt 생성 예정
```

## 테스트
```bash
# 프로그램 실행 테스트
python Simple_commander_v1.05.py

# 테스트 체크리스트
- [ ] 파일 복사 동작
- [ ] 파일 이동 동작
- [ ] 파일 삭제 동작
- [ ] 다중 선택 동작
- [ ] 검색 기능 동작
- [ ] 압축/해제 동작
```

## 라이선스

이 프로젝트에 기여하면 [MIT License](LICENSE)에 동의하는 것으로 간주됩니다.

## 질문이나 도움이 필요하신가요?

- 💬 Issue를 열어 질문해주세요
- 📧 이메일: yongsub@gmail.com (선택사항)
- 💡 Discussion 탭을 이용해주세요

## 행동 강령

### 우리의 약속

- 🤝 모든 기여자를 존중합니다
- 💬 건설적인 피드백을 제공합니다
- 🌍 다양성을 환영합니다
- 🎯 프로젝트 개선에 집중합니다

### 금지 행동

- ❌ 괴롭힘, 차별, 모욕
- ❌ 개인 정보 무단 공개
- ❌ 스팸, 광고
- ❌ 악의적인 행동

## 감사합니다! 🙏

여러분의 기여가 Simple Commander를 더 좋은 프로젝트로 만듭니다!

---

**Happy Coding! 🚀**
