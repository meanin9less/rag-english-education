# 📚 RAG 기반 영어 교육 콘텐츠 생성 시스템

중학교 영어 교육을 위한 AI 기반 지문 및 예문 생성 시스템입니다.

## 🎯 주요 기능

### 📊 데이터베이스 구조
- **문법 데이터**: 17개 카테고리, 56개 주제, 84개 성취기준
- **독해 유형**: 다양한 독해 기능별 분류
- **어휘 데이터**: 3,090개 단어 (basic/middle/high 레벨별 분류)
- **사용자 관리**: 사용자 정보 및 채팅 히스토리

### 🤖 AI 콘텐츠 생성
- **다양한 프롬프트 템플릿**: 기본/문법/어휘/독해 유형별
- **난이도별 단어 추출**: 학습자 수준에 맞는 어휘 선별
- **구조화된 JSON 응답**: 교육적 활용이 용이한 형태

## 🚀 설치 및 설정

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env` 파일을 생성하고 다음 내용을 입력하세요:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```

### 3. 데이터베이스 초기화
```bash
python main.py
```

## 📁 파일 구조

```
rag/
├── main.py              # 메인 실행 파일 및 핵심 기능
├── models.py            # SQLAlchemy 모델 정의
├── prompts.py           # AI 프롬프트 템플릿 관리
├── requirements.txt     # Python 패키지 의존성
├── basic.txt           # 기초 수준 단어 목록 (852개)
├── middle.txt          # 중급 수준 단어 목록 (1,219개)
├── high.txt            # 고급 수준 단어 목록 (1,035개)
├── .env                # 환경변수 (직접 생성 필요)
├── .gitignore          # Git 무시 파일 목록
└── README.md           # 프로젝트 설명서
```

## 🔧 사용 방법

### 1. 기본 지문 생성
```python
from main import generate_content_with_prompt

response = generate_content_with_prompt(
    prompt_type="basic",
    학년="중학교",
    학급="1학년",
    지문길이="100~120단어",
    예문길이="20단어",
    어휘수준="중학교 1학년 수준",
    소재="학교생활",
    글종류="일반적인 글",
    독해유형="주제 추론",
    어휘유형="일상어휘",
    문법유형="현재시제",
    추가요청="친근하고 재미있는 내용으로"
)
```

### 2. 난이도별 단어 추출
```python
from main import setup_database, get_word_list_by_difficulty

db_manager = setup_database()

# 중학교 1학년 중간 수준으로 200개 단어 추출
words = get_word_list_by_difficulty(db_manager, '중간', 200)
```

## 📊 난이도별 단어 비율

| 난이도 | Basic | Middle | High | 설명 |
|--------|-------|---------|------|------|
| 하 | 40% | 60% | 0% | 중학교 1학년 하위권 |
| 중간 | 30% | 70% | 0% | 중학교 1학년 중위권 |
| 상 | 10% | 60% | 30% | 중학교 1학년 상위권 |

## 🎨 프롬프트 템플릿 유형

1. **basic**: 기본 지문 생성 프롬프트
2. **grammar**: 문법 중심 지문 생성 프롬프트
3. **vocabulary**: 어휘 중심 지문 생성 프롬프트
4. **reading**: 독해 유형별 지문 생성 프롬프트

## 📈 데이터베이스 테이블

### 문법 관련
- `grammar_categories`: 문법 카테고리 (17개)
- `grammar_topics`: 문법 주제 (56개)
- `grammar_achievements`: 문법 성취기준 (84개)

### 독해 및 어휘
- `reading_types`: 독해 유형
- `vocabulary_categories`: 어휘 카테고리
- `vocabulary_achievements`: 어휘 성취기준
- `words`: 단어 목록 (3,090개)

### 사용자 관리
- `users`: 사용자 정보
- `chat_history`: 채팅 히스토리

## 🛠 기술 스택

- **Python 3.x**
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **PostgreSQL**: 메인 데이터베이스
- **Google Gemini API**: AI 콘텐츠 생성
- **python-dotenv**: 환경변수 관리

## 📝 라이센스

이 프로젝트는 교육 목적으로 개발되었습니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.
