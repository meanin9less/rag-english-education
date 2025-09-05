# 기본 지문 생성 프롬프트
CONTENT_GENERATION_PROMPT = """
**[지시문]**

당신은 {학년} {학급} 영어 교육을 위한 지문, 예문 생성 AI입니다. 다음 조건에 맞춰 퀄리티 있는 영어 지문을 생성해 주세요.

**[생성 조건]**

1. **지문의 길이**: {지문길이} 내외
2. **예문의 길이**: {예문길이} 내외
3. **어휘 수준**: {어휘수준} (다음 단어들을 우선적으로 사용: {단어목록})
4. **소재**: {소재}
5. **글 종류**: {글종류}
6. **출제의도**: 각 영역별로 지문, 예문의 출제의도를 남겨야함
    - 독해: {독해유형}
    - 어휘: {어휘유형}
    - 문법: {문법유형}
7. **응답 형식**: 아래 JSON 구조를 반드시 준수하여 출력해 주세요.
8. **추가 요청사항**: {추가요청}

**[JSON 응답 형식]**

위 형식을 정확히 준수하여 교육적 가치가 높은 영어 콘텐츠를 생성해 주세요.
"""

def get_prompt_template(prompt_type="basic"):
    """
    프롬프트 템플릿을 반환하는 함수
    
    Args:
        prompt_type: 프롬프트 유형 ("basic", "grammar", "vocabulary", "reading")
    
    Returns:
        str: 선택된 프롬프트 템플릿
    """
    templates = {
        "basic": CONTENT_GENERATION_PROMPT,
        "grammar": GRAMMAR_FOCUSED_PROMPT,
        "vocabulary": VOCABULARY_FOCUSED_PROMPT,
        "reading": READING_TYPE_PROMPT
    }
    
    return templates.get(prompt_type, CONTENT_GENERATION_PROMPT)

def format_prompt(prompt_type="basic", **kwargs):
    """
    프롬프트 템플릿에 값을 채워서 반환하는 함수
    
    Args:
        prompt_type: 프롬프트 유형
        **kwargs: 프롬프트에 채울 값들
    
    Returns:
        str: 완성된 프롬프트
    """
    template = get_prompt_template(prompt_type)
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        print(f"프롬프트 포맷팅 오류: {e} 키가 누락되었습니다.")
        return template
