import google.generativeai as genai
import os
import time
import json
import re
from dotenv import load_dotenv
from models import (DatabaseConfig, DatabaseManager, User, ChatHistory, 
                   GrammarCategory, GrammarTopic, GrammarAchievement, 
                   ReadingType, VocabularyCategory, VocabularyAchievement, Word,
                   ContentGenerationRequest, QuestionDistribution)

# .env 파일 로드
load_dotenv()

# 제미나이 API 키 설정 (환경변수에서 가져오기)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# 제미나이 모델 생성
model = genai.GenerativeModel('gemini-2.5-pro')

# 프롬프트는 prompts.py 파일에서 관리
from prompts import get_prompt, format_prompt

def generate_response(prompt):
    """제미나이 모델을 사용해 응답 생성"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"오류 발생: {str(e)}"

def generate_content_with_prompt(prompt_type, **kwargs):
    """
    프롬프트 템플릿을 사용해 콘텐츠 생성
    
    Args:
        prompt_type: 프롬프트 유형 ("passage", "question", "answer")
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

def get_reading_types(db_manager):
    """독해 유형 조회"""
    session = db_manager.get_session()
    try:
        reading_types = session.query(ReadingType).order_by(ReadingType.order_num).all()
        return reading_types
    finally:
        session.close()

def get_vocabulary_categories(db_manager):
    """어휘 카테고리 조회"""
    session = db_manager.get_session()
    try:
        categories = session.query(VocabularyCategory).order_by(VocabularyCategory.order_num).all()
        return categories
    finally:
        session.close()

def get_vocabulary_achievements_by_category(db_manager, category_id):
    """카테고리별 어휘 성취기준 조회"""
    session = db_manager.get_session()
    try:
        achievements = session.query(VocabularyAchievement).filter(
            VocabularyAchievement.category_id == category_id
        ).all()
        return achievements
    finally:
        session.close()

def get_words_by_level(db_manager, level):
    """레벨별 단어 조회"""
    session = db_manager.get_session()
    try:
        words = session.query(Word).filter(Word.level == level).all()
        return [word.word for word in words]
    finally:
        session.close()

def calculate_question_distribution(request: ContentGenerationRequest):
    """문항 수 계산 및 분배"""
    distributions = []
    
    # 1. 카테고리별 기본 문항 수 계산
    total_ratio = sum(cat.ratio for cat in request.categories)
    
    for category in request.categories:
        # 카테고리별 문항 수
        category_questions = int(request.total_questions * category.ratio / total_ratio)
        
        # 세부 카테고리별 문항 수 (균등 분배)
        subcategory_questions = category_questions // len(category.subcategories)
        remaining = category_questions % len(category.subcategories)
        
        for i, subcategory in enumerate(category.subcategories):
            # 나머지는 앞쪽 세부 카테고리에 배분
            questions_for_subcategory = subcategory_questions + (1 if i < remaining else 0)
            
            # 난이도별 분배
            if request.difficulty == "분배":
                high_count = max(1, int(questions_for_subcategory * request.difficulty_distribution.high / 100))
                low_count = max(1, int(questions_for_subcategory * request.difficulty_distribution.low / 100))
                medium_count = questions_for_subcategory - high_count - low_count
                
                # 각 난이도별로 QuestionDistribution 생성
                if high_count > 0:
                    distributions.append(QuestionDistribution(category.name, subcategory, high_count, "상"))
                if medium_count > 0:
                    distributions.append(QuestionDistribution(category.name, subcategory, medium_count, "중"))
                if low_count > 0:
                    distributions.append(QuestionDistribution(category.name, subcategory, low_count, "하"))
            else:
                # 단일 난이도
                distributions.append(QuestionDistribution(category.name, subcategory, questions_for_subcategory, request.difficulty))
    
    return distributions

def print_question_distribution(distributions):
    """문제 분배 결과 출력"""
    print("\n📊 문제 분배 계획:")
    print("=" * 50)
    
    category_totals = {}
    difficulty_totals = {"상": 0, "중": 0, "하": 0}
    
    for dist in distributions:
        # 카테고리별 집계
        if dist.category not in category_totals:
            category_totals[dist.category] = 0
        category_totals[dist.category] += dist.count
        
        # 난이도별 집계
        if dist.difficulty_level in difficulty_totals:
            difficulty_totals[dist.difficulty_level] += dist.count
        
        print(f"  {dist.category} > {dist.subcategory} ({dist.difficulty_level}): {dist.count}문항")
    
    print("\n📋 카테고리별 요약:")
    for category, count in category_totals.items():
        print(f"  {category}: {count}문항")
    
    print("\n🎯 난이도별 요약:")
    for difficulty, count in difficulty_totals.items():
        if count > 0:
            print(f"  {difficulty}: {count}문항")
    
    total = sum(dist.count for dist in distributions)
    print(f"\n📝 총 문항 수: {total}문항")
    print("=" * 50)

def process_user_request_new(db_manager, request_data):
    """
    새로운 구조의 사용자 요청을 처리하여 영어 학습 콘텐츠를 생성합니다.
    
    Args:
        db_manager: 데이터베이스 매니저
        request_data: ContentGenerationRequest 객체 또는 딕셔너리
    
    Returns:
        dict: 생성된 콘텐츠 (지문, 예문, 문제, 답안)
    """
    # 딕셔너리인 경우 객체로 변환
    if isinstance(request_data, dict):
        request = ContentGenerationRequest(**request_data)
    else:
        request = request_data
    
    print(f"========== 새로운 구조 사용자 요청 처리 시작 ==========")
    print(f"학년: {request.grade}학년")
    print(f"문제 유형: {request.question_type}")
    print(f"난이도: {request.difficulty}")
    print(f"총 문항 수: {request.total_questions}")
    
    print(f"\n카테고리 구성:")
    for cat in request.categories:
        print(f"  - {cat.name} ({cat.ratio}%): {', '.join(cat.subcategories)}")
    
    # 1. 문항 분배 계산
    distributions = calculate_question_distribution(request)
    print_question_distribution(distributions)
    
    # 2. 데이터베이스에서 정보 조회
    db_info = gather_db_info_new(db_manager, request)
    
    # 3. 분배별로 콘텐츠 생성
    all_results = generate_content_by_distribution(db_manager, request, distributions, db_info)
    
    return all_results

def process_user_request(db_manager, grade, categories, difficulty, grammar_subcategories=None):
    """
    기존 호환성을 위한 함수 (레거시 지원)
    """
    print(f"========== 기존 구조 사용자 요청 처리 시작 ==========")
    print(f"학년: {grade}")
    print(f"카테고리: {categories}")
    print(f"난이도: {difficulty}")
    if grammar_subcategories:
        print(f"문법 소분류: {grammar_subcategories}")
    
    # 1. 데이터베이스에서 정보 조회
    db_info = gather_db_info(db_manager, categories, difficulty, grammar_subcategories)
    
    # 2. 프롬프트 매개변수 생성
    prompt_params = build_prompt_params(grade, categories, difficulty, db_info)
    
    # 3. 콘텐츠 생성
    result = generate_learning_content(prompt_params)
    
    return result

def gather_db_info(db_manager, categories, difficulty, grammar_subcategories=None):
    """데이터베이스에서 필요한 정보를 수집합니다."""
    db_info = {
        'grammar_points': [],
        'reading_types': [],
        'vocabulary_info': [],
        'word_list': []
    }
    
    # 난이도에 따른 어휘 레벨 매핑
    level_mapping = {
        "기본": "basic",
        "중간": "middle", 
        "고급": "high"
    }
    word_level = level_mapping.get(difficulty, "basic")
    
    # 단어 목록 조회
    db_info['word_list'] = get_words_by_level(db_manager, word_level)[:20]  # 상위 20개만
    
    for category in categories:
        if category == "문법":
            if grammar_subcategories:
                # 특정 문법 소분류가 지정된 경우
                for subcategory in grammar_subcategories:
                    # 실제 구현에서는 subcategory 이름으로 DB 조회
                    db_info['grammar_points'].append(subcategory)
            else:
                # 전체 문법 카테고리에서 랜덤 선택
                grammar_categories = get_grammar_categories(db_manager)
                if grammar_categories:
                    # 첫 번째 카테고리의 주제들 조회
                    topics = get_grammar_topics_by_category(db_manager, grammar_categories[0].id)
                    if topics:
                        db_info['grammar_points'].append(topics[0].name)
        
        elif category == "독해":
            reading_types = get_reading_types(db_manager)
            if reading_types:
                db_info['reading_types'].extend([rt.name for rt in reading_types[:3]])
        
        elif category == "어휘":
            vocab_categories = get_vocabulary_categories(db_manager)
            if vocab_categories:
                db_info['vocabulary_info'].append(vocab_categories[0].name)
    
    return db_info

def gather_db_info_new(db_manager, request: ContentGenerationRequest):
    """새로운 구조를 위한 데이터베이스 정보 수집"""
    db_info = {
        'grammar_points': [],
        'reading_types': [],
        'vocabulary_info': [],
        'word_list': []
    }
    
    # 난이도에 따른 어휘 레벨 매핑
    level_mapping = {
        "상": "high",
        "중": "middle", 
        "하": "basic"
    }
    
    # 기본 단어 레벨 (분배인 경우 중간 레벨 사용)
    if request.difficulty == "분배":
        word_level = "middle"
    else:
        word_level = level_mapping.get(request.difficulty, "middle")
    
    # 단어 목록 조회
    db_info['word_list'] = get_words_by_level(db_manager, word_level)[:20]
    
    # 카테고리별 정보 수집
    for category in request.categories:
        if category.name == "문법":
            for subcategory in category.subcategories:
                db_info['grammar_points'].append(subcategory)
        
        elif category.name == "독해":
            for subcategory in category.subcategories:
                db_info['reading_types'].append(subcategory)
        
        elif category.name == "어휘":
            for subcategory in category.subcategories:
                db_info['vocabulary_info'].append(subcategory)
    
    return db_info

def generate_content_by_distribution(db_manager, request: ContentGenerationRequest, distributions, db_info):
    """분배 계획에 따라 콘텐츠 생성"""
    all_results = {
        'passages': [],
        'sentences': [],
        'questions': [],
        'answers': [],
        'distributions': distributions
    }
    
    print(f"\n🚀 분배 계획에 따른 콘텐츠 생성 시작")
    
    # 각 분배별로 콘텐츠 생성
    for i, dist in enumerate(distributions):
        print(f"\n📝 [{i+1}/{len(distributions)}] {dist.category} > {dist.subcategory} ({dist.difficulty_level}) - {dist.count}문항 생성 중...")
        
        # 해당 분배에 맞는 프롬프트 매개변수 생성
        params = build_prompt_params_for_distribution(request, dist, db_info)
        
        # 지문 및 예문 생성 (각 분배마다 별도 생성)
        passage_result = generate_content_with_prompt("passage", **params)
        
        if passage_result and "오류 발생" not in passage_result:
            try:
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', passage_result, re.DOTALL)
                if json_match:
                    passage_data = json.loads(json_match.group(1))
                    
                    # 결과에 추가 (분배 정보와 함께)
                    for passage in passage_data.get("passages", []):
                        passage['distribution_info'] = f"{dist.category}-{dist.subcategory}-{dist.difficulty_level}"
                        all_results['passages'].append(passage)
                    
                    for sentence in passage_data.get("sentences", []):
                        sentence['distribution_info'] = f"{dist.category}-{dist.subcategory}-{dist.difficulty_level}"
                        all_results['sentences'].append(sentence)
                    
                    print(f"✅ 지문 {len(passage_data.get('passages', []))}개, 예문 {len(passage_data.get('sentences', []))}개 생성 완료")
                    
            except Exception as e:
                print(f"❌ 분배 {i+1} 처리 중 오류: {e}")
                continue
    
    # 통합된 문제 생성 (모든 지문과 예문을 사용)
    if all_results['passages'] and all_results['sentences']:
        print(f"\n🔍 통합 문제 생성 중... (총 {request.total_questions}문항)")
        questions_result = generate_integrated_questions(request, all_results, db_info)
        if questions_result:
            all_results.update(questions_result)
    
    return all_results

def build_prompt_params_for_distribution(request: ContentGenerationRequest, dist: QuestionDistribution, db_info):
    """특정 분배를 위한 프롬프트 매개변수 생성"""
    params = {
        "level": f"중학교 {request.grade}학년",
        "passage_count": "1",  # 분배별로 1개씩
        "passage_length": "80" if dist.difficulty_level == "하" else "100" if dist.difficulty_level == "중" else "120",
        "sentence_count": "2",
        "sentence_length": "10" if dist.difficulty_level == "하" else "12" if dist.difficulty_level == "중" else "15",
        "word_list": ", ".join(db_info['word_list'][:10]) if db_info['word_list'] else "student, study, school",
        "topic": f"{dist.category} 관련 주제",
        "grammar_point": dist.subcategory if dist.category == "문법" else "기본 문법",
        "reading_type": dist.subcategory if dist.category == "독해" else "내용 이해"
    }
    
    return params

def generate_integrated_questions(request: ContentGenerationRequest, content_results, db_info):
    """통합된 문제 및 답안 생성"""
    # 모든 지문과 예문을 하나의 텍스트로 통합
    passages_text = "\n\n".join([f"지문 {i+1}: {p['title']}\n{p['content']}" 
                                for i, p in enumerate(content_results['passages'])])
    sentences_text = "\n".join([f"예문 {i+1}: {s['english']}" 
                               for i, s in enumerate(content_results['sentences'])])
    
    question_params = {
        "passages": passages_text,
        "sentences": sentences_text,
        "question_count": str(request.total_questions),
        "question_type": request.question_type,
        "learning_objective": f"다양한 카테고리의 종합적 이해 평가"
    }
    
    try:
        # 문제 생성
        question_response = generate_content_with_prompt("question", **question_params)
        
        if question_response and "오류 발생" not in question_response:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', question_response, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group(1))
                questions = question_data.get("questions", [])
                
                if questions:
                    # 답안 생성
                    questions_text = ""
                    for q in questions:
                        questions_text += f"문제 {q['id']}: {q['question']}\n"
                        if 'modified_passage' in q and q['modified_passage']:
                            questions_text += f"변형된 지문: {q['modified_passage']}\n"
                        questions_text += "\n".join(q['choices']) + "\n\n"
                    
                    answer_params = {
                        "passages": passages_text,
                        "sentences": sentences_text,
                        "questions": questions_text
                    }
                    
                    answer_response = generate_content_with_prompt("answer", **answer_params)
                    
                    if answer_response and "오류 발생" not in answer_response:
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', answer_response, re.DOTALL)
                        if json_match:
                            answer_data = json.loads(json_match.group(1))
                            answers = answer_data.get("answers", [])
                            
                            return {
                                'questions': questions,
                                'answers': answers
                            }
    
    except Exception as e:
        print(f"❌ 통합 문제 생성 중 오류: {e}")
    
    return {}

def build_prompt_params(grade, categories, difficulty, db_info):
    """프롬프트 매개변수를 구성합니다."""
    
    # 기본 매개변수
    params = {
        "level": grade,
        "passage_count": "2",
        "passage_length": "80",
        "sentence_count": "3",
        "sentence_length": "12",
        "word_list": ", ".join(db_info['word_list'][:10]) if db_info['word_list'] else "student, study, school",
        "topic": "학교 생활과 일상"
    }
    
    # 카테고리별 정보 추가
    if "문법" in categories and db_info['grammar_points']:
        params["grammar_point"] = db_info['grammar_points'][0]
    else:
        params["grammar_point"] = "현재시제와 과거시제"
    
    if "독해" in categories and db_info['reading_types']:
        params["reading_type"] = ", ".join(db_info['reading_types'])
    else:
        params["reading_type"] = "주제/제목 추론"
    
    # 난이도별 조정
    if difficulty == "고급":
        params["passage_length"] = "120"
        params["sentence_length"] = "15"
        params["question_count"] = "4"
    elif difficulty == "중간":
        params["passage_length"] = "100"
        params["sentence_length"] = "13"
        params["question_count"] = "3"
    else:  # 기본
        params["passage_length"] = "80"
        params["sentence_length"] = "12"
        params["question_count"] = "2"
    
    return params

def generate_learning_content(params):
    """프롬프트 매개변수를 사용하여 학습 콘텐츠를 생성합니다."""
    result = {}
    
    try:
        # 1. 지문 및 예문 생성
        print("\n========== 지문 및 예문 생성 중 ==========")
        passage_response = generate_content_with_prompt("passage", **params)
        
        if passage_response and "오류 발생" not in passage_response:
            # JSON 파싱
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', passage_response, re.DOTALL)
            if json_match:
                passage_data = json.loads(json_match.group(1))
                result['passages'] = passage_data.get("passages", [])
                result['sentences'] = passage_data.get("sentences", [])
                
                # 2. 문제 생성
                print("========== 문제 생성 중 ==========")
                passages_text = "\n\n".join([f"지문 {i+1}: {p['title']}\n{p['content']}" 
                                           for i, p in enumerate(result['passages'])])
                sentences_text = "\n".join([f"예문 {i+1}: {s['english']}" 
                                          for i, s in enumerate(result['sentences'])])
                
                question_params = {
                    "passages": passages_text,
                    "sentences": sentences_text,
                    "question_count": params.get("question_count", "3"),
                    "question_type": "객관식 4지선다",
                    "learning_objective": f"{params.get('reading_type', '독해')} 및 {params.get('grammar_point', '문법')} 이해 평가"
                }
                
                question_response = generate_content_with_prompt("question", **question_params)
                
                if question_response and "오류 발생" not in question_response:
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', question_response, re.DOTALL)
                    if json_match:
                        question_data = json.loads(json_match.group(1))
                        result['questions'] = question_data.get("questions", [])
                        
                        # 3. 답안 생성
                        print("========== 답안 생성 중 ==========")
                        questions_text = ""
                        for q in result['questions']:
                            questions_text += f"문제 {q['id']}: {q['question']}\n"
                            questions_text += "\n".join(q['choices']) + "\n\n"
                        
                        answer_params = {
                            "passages": passages_text,
                            "sentences": sentences_text,
                            "questions": questions_text
                        }
                        
                        answer_response = generate_content_with_prompt("answer", **answer_params)
                        
                        if answer_response and "오류 발생" not in answer_response:
                            json_match = re.search(r'```json\s*(\{.*?\})\s*```', answer_response, re.DOTALL)
                            if json_match:
                                answer_data = json.loads(json_match.group(1))
                                result['answers'] = answer_data.get("answers", [])
        
        print("========== 콘텐츠 생성 완료 ==========")
        return result
        
    except Exception as e:
        print(f"콘텐츠 생성 중 오류 발생: {e}")
        return {"error": str(e)}

def run_test_scenario():
    """엔드투엔드 프롬프트 생성 및 LLM 호출 테스트"""
    print("========== 1. 지문 및 예문 생성 테스트 시작 ==========")
    
    # 1. 지문 및 예문 생성
    passage_params = {
        "level": "중학교 1학년",
        "passage_count": "2",
        "passage_length": "80",
        "sentence_count": "3", 
        "sentence_length": "12",
        "word_list": "student, study, school, teacher, future, dream, important, help",
        "grammar_point": "to부정사의 명사적 용법 (주어, 목적어, 보어)",
        "reading_type": "주제/제목 추론, 세부사항 파악",
        "topic": "학교 생활과 장래 희망"
    }
    
    passage_response_str = generate_content_with_prompt("passage", **passage_params)
    print("--- [AI 응답 원본 (지문)] ---")
    print(passage_response_str)
    
    if not passage_response_str or "오류 발생" in passage_response_str:
        print("\n[오류] 지문 생성에 실패했습니다.")
        return

    try:
        # 응답 문자열에서 JSON 부분만 추출
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', passage_response_str, re.DOTALL)
        if json_match:
            passage_json_str = json_match.group(1)
        else:
            # 마크다운 코드 블록이 없는 경우 전체를 JSON으로 시도
            passage_json_str = passage_response_str.strip()
        
        passage_data = json.loads(passage_json_str)
        passages = passage_data.get("passages", [])
        sentences = passage_data.get("sentences", [])
        if not passages or not sentences:
            raise ValueError("JSON 응답에서 'passages' 또는 'sentences'를 찾을 수 없습니다.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"\n[오류] 지문 응답 JSON 파싱 오류: {e}")
        print("파싱에 실패하여 테스트를 종료합니다.")
        return
    except Exception as e:
        print(f"\n[오류] 지문 처리 중 알 수 없는 오류 발생: {e}")
        return

    print("\n========== 2. 문제 생성 테스트 시작 ==========")

    # 2. 문제 생성 (지문과 예문을 모두 활용)
    passages_text = "\n\n".join([f"지문 {i+1}: {p['title']}\n{p['content']}" for i, p in enumerate(passages)])
    sentences_text = "\n".join([f"예문 {i+1}: {s['english']}" for i, s in enumerate(sentences)])
    
    question_params = {
        "passages": passages_text,
        "sentences": sentences_text,
        "question_count": "3",
        "question_type": "객관식 4지선다",
        "learning_objective": "지문과 예문을 통해 주제 파악, 세부사항 이해, 문법 적용 능력 평가"
    }

    question_response_str = generate_content_with_prompt("question", **question_params)
    print("--- [AI 응답 원본 (문제)] ---")
    print(question_response_str)

    if not question_response_str or "오류 발생" in question_response_str:
        print("\n[오류] 문제 생성에 실패했습니다.")
        return

    try:
        # 응답 문자열에서 JSON 부분만 추출
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', question_response_str, re.DOTALL)
        if json_match:
            question_json_str = json_match.group(1)
        else:
            # 마크다운 코드 블록이 없는 경우 전체를 JSON으로 시도
            question_json_str = question_response_str.strip()
        
        question_data = json.loads(question_json_str)
        questions = question_data.get("questions", [])
        if not questions:
             raise ValueError("JSON 응답에서 'questions'를 찾을 수 없습니다.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"\n[오류] 문제 응답 JSON 파싱 오류: {e}")
        return
    except Exception as e:
        print(f"\n[오류] 문제 처리 중 알 수 없는 오류 발생: {e}")
        return

    print("\n========== 3. 답안 생성 테스트 시작 ==========")

    # 3. 답안 생성 (모든 문제를 한 번에 채점)
    questions_text = ""
    for q in questions:
        questions_text += f"문제 {q['id']}: {q['question']}\n"
        questions_text += "\n".join(q['choices']) + "\n\n"
    
    answer_params = {
        "passages": passages_text,
        "sentences": sentences_text,
        "questions": questions_text
    }

    answer_response_str = generate_content_with_prompt("answer", **answer_params)
    print("--- [AI 응답 원본 (답안)] ---")
    print(answer_response_str)
    
    print("\n========== 테스트 종료 ==========")

def test_scenario_3_detailed():
    """테스트 시나리오 3을 상세하게 실행하고 각 단계별 결과를 출력"""
    print("========== 테스트 시나리오 3 상세 실행 ==========")
    print("문법 + 독해 + 어휘 (고급 난이도)")
    print("학년: 중학교 3학년")
    print("문법 소분류: 현재완료시제, 관계대명사")
    print("=" * 60)
    
    # 데이터베이스 연결
    print("\n🔗 데이터베이스 연결 중...")
    db_manager = setup_database()
    
    if not db_manager:
        print("❌ 데이터베이스 연결 실패로 테스트를 종료합니다.")
        return
    print("✅ 데이터베이스 연결 성공")
    
    # 1. 데이터베이스에서 정보 조회
    print("\n📊 데이터베이스에서 정보 조회 중...")
    categories = ["문법", "독해", "어휘"]
    difficulty = "고급"
    grammar_subcategories = ["현재완료시제", "관계대명사"]
    
    db_info = gather_db_info(db_manager, categories, difficulty, grammar_subcategories)
    
    print(f"  - 문법 포인트: {db_info['grammar_points']}")
    print(f"  - 독해 유형: {db_info['reading_types']}")
    print(f"  - 어휘 정보: {db_info['vocabulary_info']}")
    print(f"  - 단어 목록 (일부): {db_info['word_list'][:10]}")
    
    # 2. 프롬프트 매개변수 생성
    print("\n⚙️ 프롬프트 매개변수 생성 중...")
    prompt_params = build_prompt_params("중학교 3학년", categories, difficulty, db_info)
    
    print("  생성된 매개변수:")
    for key, value in prompt_params.items():
        print(f"    {key}: {value}")
    
    # 3. 지문 및 예문 생성
    print("\n📝 지문 및 예문 생성 중...")
    passage_response = generate_content_with_prompt("passage", **prompt_params)
    
    print("--- [AI 응답 원본 (지문 및 예문)] ---")
    print(passage_response)
    print("-" * 50)
    
    if not passage_response or "오류 발생" in passage_response:
        print("❌ 지문 생성 실패")
        return
    
    # JSON 파싱
    try:
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', passage_response, re.DOTALL)
        if json_match:
            passage_data = json.loads(json_match.group(1))
            passages = passage_data.get("passages", [])
            sentences = passage_data.get("sentences", [])
            
            print(f"✅ 지문 및 예문 생성 성공: 지문 {len(passages)}개, 예문 {len(sentences)}개")
            
            # 생성된 지문과 예문 출력
            for i, passage in enumerate(passages):
                print(f"\n📖 지문 {i+1}: {passage['title']}")
                print(f"   내용: {passage['content']}")
                print(f"   번역: {passage['korean_translation']}")
            
            for i, sentence in enumerate(sentences):
                print(f"\n💬 예문 {i+1}: {sentence['english']}")
                print(f"   번역: {sentence['korean']}")
        else:
            print("❌ JSON 파싱 실패")
            return
    except Exception as e:
        print(f"❌ 지문 파싱 중 오류: {e}")
        return
    
    # 4. 문제 생성
    print("\n❓ 문제 생성 중...")
    passages_text = "\n\n".join([f"지문 {i+1}: {p['title']}\n{p['content']}" for i, p in enumerate(passages)])
    sentences_text = "\n".join([f"예문 {i+1}: {s['english']}" for i, s in enumerate(sentences)])
    
    question_params = {
        "passages": passages_text,
        "sentences": sentences_text,
        "question_count": prompt_params.get("question_count", "4"),
        "question_type": "객관식 4지선다",
        "learning_objective": f"{prompt_params.get('reading_type', '독해')} 및 {prompt_params.get('grammar_point', '문법')} 이해 평가"
    }
    
    question_response = generate_content_with_prompt("question", **question_params)
    
    print("--- [AI 응답 원본 (문제)] ---")
    print(question_response)
    print("-" * 50)
    
    if not question_response or "오류 발생" in question_response:
        print("❌ 문제 생성 실패")
        return
    
    # 문제 JSON 파싱
    try:
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', question_response, re.DOTALL)
        if json_match:
            question_data = json.loads(json_match.group(1))
            questions = question_data.get("questions", [])
            
            print(f"✅ 문제 생성 성공: {len(questions)}개")
            
            # 생성된 문제 출력
            for i, q in enumerate(questions):
                print(f"\n🔍 문제 {q['id']}: {q['question']}")
                
                # 변형된 지문이 있는 경우 출력
                if 'modified_passage' in q and q['modified_passage']:
                    print(f"   📝 변형된 지문: {q['modified_passage']}")
                
                # 변형 유형 출력
                if 'modification_type' in q:
                    print(f"   🔧 변형 유형: {q['modification_type']}")
                
                for choice in q['choices']:
                    print(f"     {choice}")
                print(f"   출처: {q.get('source', '알 수 없음')}")
        else:
            print("❌ 문제 JSON 파싱 실패")
            return
    except Exception as e:
        print(f"❌ 문제 파싱 중 오류: {e}")
        return
    
    # 5. 답안 생성
    print("\n✅ 답안 생성 중...")
    questions_text = ""
    for q in questions:
        questions_text += f"문제 {q['id']}: {q['question']}\n"
        
        # 변형된 지문이 있는 경우 포함
        if 'modified_passage' in q and q['modified_passage']:
            questions_text += f"변형된 지문: {q['modified_passage']}\n"
        
        # 변형 유형 정보 포함
        if 'modification_type' in q:
            questions_text += f"변형 유형: {q['modification_type']}\n"
        
        questions_text += "\n".join(q['choices']) + "\n\n"
    
    answer_params = {
        "passages": passages_text,
        "sentences": sentences_text,
        "questions": questions_text
    }
    
    answer_response = generate_content_with_prompt("answer", **answer_params)
    
    print("--- [AI 응답 원본 (답안)] ---")
    print(answer_response)
    print("-" * 50)
    
    if answer_response and "오류 발생" not in answer_response:
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', answer_response, re.DOTALL)
            if json_match:
                answer_data = json.loads(json_match.group(1))
                answers = answer_data.get("answers", [])
                
                print(f"✅ 답안 생성 성공: {len(answers)}개")
                
                # 생성된 답안 출력
                for answer in answers:
                    print(f"\n🎯 문제 {answer['question_id']} 정답: {answer['correct_choice']}")
                    print(f"   해설: {answer['explanation']['main'][:100]}...")
                    print(f"   학습포인트: {answer['explanation']['learning_point'][:100]}...")
            else:
                print("❌ 답안 JSON 파싱 실패")
        except Exception as e:
            print(f"❌ 답안 파싱 중 오류: {e}")
    else:
        print("❌ 답안 생성 실패")
    
    print("\n🎉 테스트 시나리오 3 완료!")
    print("=" * 60)

def test_new_structure():
    """새로운 입력 구조를 테스트하는 함수"""
    print("========== 새로운 입력 구조 테스트 시작 ==========")
    
    # 데이터베이스 연결
    db_manager = setup_database()
    
    if not db_manager:
        print("❌ 데이터베이스 연결 실패로 테스트를 종료합니다.")
        return
    
    # 테스트 요청 데이터 구성
    test_request = {
        "grade": 2,
        "categories": [
            {
                "name": "독해",
                "subcategories": ["주제/제목 추론", "세부사항 파악"],
                "ratio": 50
            },
            {
                "name": "문법", 
                "subcategories": ["현재완료시제", "관계대명사"],
                "ratio": 30
            },
            {
                "name": "어휘",
                "subcategories": ["문맥상 적절한 어휘"],
                "ratio": 20
            }
        ],
        "question_type": "객관식",
        "difficulty": "분배",
        "difficulty_distribution": {
            "high": 20,    # 상
            "medium": 60,  # 중
            "low": 20      # 하
        },
        "total_questions": 10
    }
    
    print("\n📋 테스트 요청 데이터:")
    print(f"  학년: {test_request['grade']}학년")
    print(f"  문제 유형: {test_request['question_type']}")
    print(f"  난이도: {test_request['difficulty']}")
    print(f"  총 문항: {test_request['total_questions']}개")
    print("  카테고리 구성:")
    for cat in test_request['categories']:
        print(f"    - {cat['name']} ({cat['ratio']}%): {', '.join(cat['subcategories'])}")
    print(f"  난이도 분배: 상({test_request['difficulty_distribution']['high']}%) 중({test_request['difficulty_distribution']['medium']}%) 하({test_request['difficulty_distribution']['low']}%)")
    
    # 새로운 구조로 콘텐츠 생성
    try:
        result = process_user_request_new(db_manager, test_request)
        
        if result and 'error' not in result:
            print(f"\n🎉 새로운 구조 테스트 성공!")
            print(f"  📖 생성된 지문: {len(result.get('passages', []))}개")
            print(f"  💬 생성된 예문: {len(result.get('sentences', []))}개") 
            print(f"  ❓ 생성된 문제: {len(result.get('questions', []))}개")
            print(f"  ✅ 생성된 답안: {len(result.get('answers', []))}개")
            
            # 생성된 지문 요약 출력
            print(f"\n📚 생성된 지문 요약:")
            for i, passage in enumerate(result.get('passages', [])):
                print(f"  {i+1}. {passage.get('title', '제목 없음')} [{passage.get('distribution_info', '정보 없음')}]")
            
            # 생성된 문제 요약 출력
            print(f"\n🔍 생성된 문제 요약:")
            for i, question in enumerate(result.get('questions', [])):
                print(f"  {question.get('id', i+1)}. {question.get('question', '질문 없음')[:50]}...")
                if 'modification_type' in question:
                    print(f"      변형 유형: {question['modification_type']}")
            
        else:
            print(f"❌ 새로운 구조 테스트 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
    
    print("\n========== 새로운 입력 구조 테스트 완료 ==========")

# 테스트
if __name__ == "__main__":
    # API 키가 설정되었는지 확인
    if not os.getenv('GEMINI_API_KEY'):
        print("GEMINI_API_KEY 환경변수를 설정해주세요.")
    else:
        print("새로운 입력 구조를 테스트합니다.")
        test_new_structure()
        
        # 기존 테스트도 실행하고 싶다면 주석 해제
        # print("\n기존 테스트 시나리오도 실행합니다.")
        # test_scenario_3_detailed()
