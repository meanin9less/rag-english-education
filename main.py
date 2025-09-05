import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
from models import (DatabaseConfig, DatabaseManager, User, ChatHistory, 
                   GrammarCategory, GrammarTopic, GrammarAchievement, 
                   ReadingType, VocabularyCategory, VocabularyAchievement, Word)

# .env 파일 로드
load_dotenv()

# 제미나이 API 키 설정 (환경변수에서 가져오기)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# 제미나이 모델 생성
model = genai.GenerativeModel('gemini-2.5-pro')

# 프롬프트는 prompts.py 파일에서 관리
from prompts import get_prompt_template, format_prompt

def generate_response(prompt):
    """제미나이 모델을 사용해 응답 생성"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"오류 발생: {str(e)}"

def generate_content_with_prompt(prompt_type="basic", **kwargs):
    """
    프롬프트 템플릿을 사용해 콘텐츠 생성
    
    Args:
        prompt_type: 프롬프트 유형 ("basic", "grammar", "vocabulary", "reading")
        **kwargs: 프롬프트에 채울 파라미터들
    
    Returns:
        str: 생성된 응답
    """
    try:
        # 프롬프트 포맷팅
        formatted_prompt = format_prompt(prompt_type, **kwargs)
        
        # 응답 생성
        response = generate_response(formatted_prompt)
        return response
    except Exception as e:
        print(f"콘텐츠 생성 오류: {e}")
        return None

# 데이터베이스 설정
def setup_database():
    """데이터베이스 연결 설정"""
    config = DatabaseConfig(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', ''),
        username=os.getenv('DB_USER', ''),
        password=os.getenv('DB_PASSWORD', '')
    )
    
    db_manager = DatabaseManager(config)
    if db_manager.connect():
        print("데이터베이스 연결 성공")
        db_manager.create_tables()
        return db_manager
    else:
        print("데이터베이스 연결 실패")
        return None

# SQLAlchemy CRUD 함수들
def create_user(db_manager, username, email):
    """사용자 생성"""
    session = db_manager.get_session()
    try:
        new_user = User(username=username, email=email)
        session.add(new_user)
        session.commit()
        print(f"사용자 생성: {username}")
        return new_user.id
    except Exception as e:
        session.rollback()
        print(f"사용자 생성 오류: {e}")
        return None
    finally:
        session.close()

def get_user_by_id(db_manager, user_id):
    """ID로 사용자 조회"""
    session = db_manager.get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        return user
    finally:
        session.close()

def save_chat_history(db_manager, user_id, prompt, response):
    """채팅 기록 저장"""
    session = db_manager.get_session()
    try:
        chat = ChatHistory(user_id=user_id, prompt=prompt, response=response)
        session.add(chat)
        session.commit()
        print("채팅 기록 저장됨")
        return chat.id
    except Exception as e:
        session.rollback()
        print(f"채팅 기록 저장 오류: {e}")
        return None
    finally:
        session.close()

def get_chat_history(db_manager, user_id=None, limit=10):
    """채팅 기록 조회"""
    session = db_manager.get_session()
    try:
        query = session.query(ChatHistory)
        if user_id:
            query = query.filter(ChatHistory.user_id == user_id)
        chats = query.order_by(ChatHistory.created_at.desc()).limit(limit).all()
        return chats
    finally:
        session.close()

# 데이터 조회 함수들
def get_grammar_categories(db_manager):
    """문법 카테고리 조회"""
    session = db_manager.get_session()
    try:
        categories = session.query(GrammarCategory).order_by(GrammarCategory.order_num).all()
        return categories
    finally:
        session.close()

def get_grammar_topics_by_category(db_manager, category_id):
    """카테고리별 문법 주제 조회"""
    session = db_manager.get_session()
    try:
        topics = session.query(GrammarTopic).filter(
            GrammarTopic.category_id == category_id
        ).order_by(GrammarTopic.order_num).all()
        return topics
    finally:
        session.close()

def get_achievements_by_topic(db_manager, topic_id):
    """주제별 성취기준 조회"""
    session = db_manager.get_session()
    try:
        achievements = session.query(GrammarAchievement).filter(
            GrammarAchievement.topic_id == topic_id
        ).all()
        return achievements
    finally:
        session.close()

# 테스트
if __name__ == "__main__":
    # API 키가 설정되었는지 확인
    if not os.getenv('GEMINI_API_KEY'):
        print("GEMINI_API_KEY 환경변수를 설정해주세요.")
    else:
        # 데이터베이스 연결 및 테이블 생성
        db_manager = setup_database()
        
        if db_manager:
            print("테이블 생성 완료!")
            
            # 데이터 조회 테스트
            categories = get_grammar_categories(db_manager)
            print(f"문법 카테고리 수: {len(categories)}")
            
            if categories:
                first_category = categories[0]
                topics = get_grammar_topics_by_category(db_manager, first_category.id)
                print(f"'{first_category.name}' 카테고리의 주제 수: {len(topics)}")
        
        print("설정 완료!")
