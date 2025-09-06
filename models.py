"""
모델 클래스들을 정의하는 파일
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class DatabaseConfig:
    """데이터베이스 설정 클래스"""
    def __init__(self, host="localhost", port=5432, database="", username="", password=""):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
    
    def get_connection_url(self):
        """SQLAlchemy 연결 URL 생성"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

class DatabaseManager:
    """데이터베이스 연결 관리 클래스"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.SessionLocal = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.engine = create_engine(self.config.get_connection_url())
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            return True
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return False
    
    def create_tables(self):
        """테이블 생성"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """세션 반환"""
        if self.SessionLocal:
            return self.SessionLocal()
        return None

class GeminiModel:
    """제미나이 모델 관리 클래스"""
    def __init__(self, api_key, model_name="gemini-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
    
    def initialize(self):
        """모델 초기화"""
        pass

class PromptTemplate:
    """프롬프트 템플릿 클래스"""
    def __init__(self, name, template):
        self.name = name
        
        self.template = template
    
    def format(self, **kwargs):
        """템플릿에 값을 채워서 반환"""
        return self.template.format(**kwargs)


# SQLAlchemy 모델 예시
class User(Base):
    """사용자 테이블"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    """채팅 기록 테이블"""
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GrammarCategory(Base):
    """문법 카테고리 테이블"""
    __tablename__ = 'grammar_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 문장의 기초, 명사, 관사 등
    order_num = Column(Integer, nullable=False)  # 순서
    created_at = Column(DateTime, default=datetime.utcnow)

class GrammarTopic(Base):
    """문법 주제 테이블"""
    __tablename__ = 'grammar_topics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)  # 영어의 8품사, 문장의 5요소 등
    order_num = Column(Integer, nullable=False)  # 카테고리 내 순서
    learning_objective = Column(Text, nullable=True)  # 학습 목표
    created_at = Column(DateTime, default=datetime.utcnow)

class GrammarAchievement(Base):
    """문법 성취기준 테이블"""
    __tablename__ = 'grammar_achievements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, nullable=False)
    level = Column(String(20), nullable=False)  # 우수, 보통, 미흡
    description = Column(Text, nullable=False)  # 성취기준 설명
    created_at = Column(DateTime, default=datetime.utcnow)

class ReadingType(Base):
    """독해 유형 테이블"""
    __tablename__ = 'reading_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 주제/제목/요지 추론 등
    description = Column(Text, nullable=True)  # 유형 설명
    order_num = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class VocabularyCategory(Base):
    """어휘 카테고리 테이블"""
    __tablename__ = 'vocabulary_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 개인 및 주변 생활 등
    order_num = Column(Integer, nullable=False)
    learning_objective = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class VocabularyAchievement(Base):
    """어휘 성취기준 테이블"""
    __tablename__ = 'vocabulary_achievements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, nullable=False)
    level = Column(String(20), nullable=False)  # 우수, 보통, 미흡
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Word(Base):
    """단어 테이블"""
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False, unique=True)  # 단어
    level = Column(String(20), nullable=False)  # basic, middle, high
    created_at = Column(DateTime, default=datetime.utcnow)

# 요청 데이터 구조를 위한 클래스들 (SQLAlchemy 모델이 아닌 일반 클래스)
class CategoryRequest:
    """카테고리 요청 구조"""
    def __init__(self, name: str, subcategories: list, ratio: int):
        self.name = name
        self.subcategories = subcategories
        self.ratio = ratio

class DifficultyDistribution:
    """난이도 분배 구조"""
    def __init__(self, high: int = 20, medium: int = 60, low: int = 20):
        self.high = high  # 상
        self.medium = medium  # 중
        self.low = low  # 하

class ContentGenerationRequest:
    """콘텐츠 생성 요청 구조"""
    def __init__(self, grade: int, categories: list, question_type: str, 
                 difficulty: str, total_questions: int, difficulty_distribution: dict = None):
        self.grade = grade
        self.categories = [CategoryRequest(**cat) if isinstance(cat, dict) else cat for cat in categories]
        self.question_type = question_type
        self.difficulty = difficulty
        self.total_questions = total_questions
        
        if difficulty_distribution:
            self.difficulty_distribution = DifficultyDistribution(**difficulty_distribution)
        else:
            # 기본 분배
            self.difficulty_distribution = DifficultyDistribution()

class QuestionDistribution:
    """문제 분배 결과"""
    def __init__(self, category: str, subcategory: str, count: int, difficulty_level: str):
        self.category = category
        self.subcategory = subcategory
        self.count = count
        self.difficulty_level = difficulty_level

