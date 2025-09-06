# 1. 지문 및 예문 생성 프롬프트
PASSAGE_GENERATION_PROMPT = """
**[지시문]**

당신은 {level} 수준의 영어 학습자를 위한 교육용 지문 및 예문 생성 AI입니다.
PostgreSQL 데이터베이스에서 추출된 아래의 조건들을 충실히 반영하여, 교육적 가치가 높은 영어 지문과 예문을 생성해 주세요.

**[생성 조건]**

1.  **지문 개수**: {passage_count}개
2.  **지문 길이**: 각 지문당 {passage_length} 단어 내외
3.  **예문 개수**: {sentence_count}개
4.  **예문 길이**: 각 예문은 {sentence_length} 단어 내외
5.  **어휘 수준**: {level} (주어진 {word_list}의 단어를 최소 3개 이상 포함)
6.  **핵심 문법**: `{grammar_point}` 개념을 반드시 포함하고, 해당 문법이 사용된 문장을 지문과 예문에 각각 1개 이상 포함하세요.
7.  **독해 유형**: `{reading_type}` 유형의 질문을 만들기에 적합한 내용으로 구성하세요.
8.  **소재**: `{topic}`에 관한 내용으로 작성하세요.
9.  **응답 형식**: 아래 JSON 구조를 반드시 준수하여, `passages`와 `sentences` 필드를 채워서 응답해 주세요. 다른 설명 없이 JSON만 반환하세요.

**[JSON 응답 형식]**
```json
{{
  "passages": [
    {{
      "title": "<지문 1 제목>",
      "content": "<생성된 영어 지문 1>",
      "korean_translation": "<지문 1 한글 번역>"
    }}
  ],
  "sentences": [
    {{
      "english": "<생성된 영어 예문 1>",
      "korean": "<예문 1 한글 번역>"
    }},
    {{
      "english": "<생성된 영어 예문 2>",
      "korean": "<예문 2 한글 번역>"
    }}
  ]
}}
```
"""

# 2. 문제 생성 프롬프트
QUESTION_GENERATION_PROMPT = """
**[지시문]**

당신은 영어 문제 출제 AI입니다. 주어진 [지문들]과 [예문들], [생성 조건]에 맞춰, 학습 목표를 달성할 수 있는 완성도 높은 영어 문제들을 생성해 주세요.

**중요**: 필요에 따라 원본 지문을 문제 출제 의도에 맞게 **적절히 변형**하여 사용하세요. 예를 들어:
- 독해 문제: 지문의 일부를 빈칸으로 만들거나, 문장 순서를 바꾸거나, 핵심 단어를 다른 표현으로 바꿔서 추론 능력을 평가
- 문법 문제: 특정 문법 구조가 포함된 문장을 변형하여 문법 이해도를 평가
- 어휘 문제: 핵심 어휘를 빈칸 처리하거나 유사한 의미의 다른 단어로 바꿔서 어휘력을 평가

**[지문들]**
{passages}

**[예문들]**
{sentences}

**[생성 조건]**

1.  **문제 개수**: {question_count}개
2.  **문제 유형**: `{question_type}` (예: 객관식 4지선다, 빈칸 채우기, 서술형)
3.  **학습 목표**: `{learning_objective}` (이 문제들을 통해 평가하고자 하는 능력)
4.  **출제 가이드**:
    - 지문과 예문의 내용을 모두 활용하되, **문제 출제 의도에 맞게 변형**하여 사용하세요.
    - 각 문제는 서로 다른 관점에서 접근하되, 전체적으로 학습 목표를 달성할 수 있도록 구성하세요.
    - 선택지는 매력적인 오답을 포함해야 하며, 정답의 근거는 명확해야 합니다.
    - 학습 목표와 관련된 핵심 요소를 질문하거나 선택지에 포함하세요.
    - **변형된 지문이나 예문을 사용한 경우, 반드시 `modified_passage` 필드에 포함하세요.**
5.  **응답 형식**: 아래 JSON 구조를 반드시 준수하여 응답해 주세요. 다른 설명 없이 JSON만 반환하세요.

**[JSON 응답 형식]**
```json
{{
  "questions": [
    {{
      "id": 1,
      "question": "<문제 1의 질문 부분>",
      "modified_passage": "<문제 출제를 위해 변형된 지문이나 예문 (변형하지 않았다면 원본 그대로)>",
      "choices": [
        "(A) <선택지 1>",
        "(B) <선택지 2>",
        "(C) <선택지 3>",
        "(D) <선택지 4>"
      ],
      "source": "<지문 또는 예문 중 어느 것을 기반으로 했는지>",
      "modification_type": "<변형 유형: 빈칸 처리, 문장 순서 변경, 어휘 대체, 원본 유지 등>",
      "learning_objective": "{learning_objective}"
    }},
    {{
      "id": 2,
      "question": "<문제 2의 질문 부분>",
      "modified_passage": "<문제 출제를 위해 변형된 지문이나 예문 (변형하지 않았다면 원본 그대로)>",
      "choices": [
        "(A) <선택지 1>",
        "(B) <선택지 2>",
        "(C) <선택지 3>",
        "(D) <선택지 4>"
      ],
      "source": "<지문 또는 예문 중 어느 것을 기반으로 했는지>",
      "modification_type": "<변형 유형: 빈칸 처리, 문장 순서 변경, 어휘 대체, 원본 유지 등>",
      "learning_objective": "{learning_objective}"
    }}
  ]
}}
```
"""

# 3. 답안 및 해설 생성 프롬프트
ANSWER_GENERATION_PROMPT = """
**[지시문]**

당신은 영어 문제 해설 AI입니다. 주어진 [지문들], [예문들], [문제들]을 바탕으로, 각 문제의 명확한 [정답]과 상세한 [해설]을 생성해 주세요.

**중요**: 문제에 변형된 지문이나 예문이 포함되어 있다면, 그 변형 내용을 고려하여 해설을 작성하세요. 원본 지문과 변형된 지문의 차이점도 설명에 포함하면 학습에 도움이 됩니다.

**[지문들]**
{passages}

**[예문들]**
{sentences}

**[문제들]**
{questions}

**[생성 조건]**

1.  **정답 찾기**: 각 문제의 정답을 정확하게 찾아서 `answers` 필드에 기입하세요.
2.  **상세한 해설**:
    - 왜 그것이 정답인지 원본 지문/예문 또는 변형된 지문을 근거로 논리적으로 설명해야 합니다.
    - 지문이 변형된 경우, 그 변형의 의도와 목적도 설명에 포함하세요.
    - 오답인 선택지들이 왜 틀렸는지 간략하게 설명해야 합니다.
    - 문제의 학습 목표와 관련된 문법, 어휘, 독해 포인트를 추가로 설명하여 학습 효과를 높여주세요.
3.  **응답 형식**: 아래 JSON 구조를 반드시 준수하여 응답해 주세요. 다른 설명 없이 JSON만 반환하세요.

**[JSON 응답 형식]**
```json
{{
  "answers": [
    {{
      "question_id": 1,
      "correct_choice": "<(A), (B), (C), (D) 중 정답>",
      "explanation": {{
        "main": "<정답에 대한 상세한 해설>",
        "distractors": "<오답 선택지에 대한 간략한 설명>",
        "learning_point": "<문제와 관련된 추가 학습 포인트 (문법, 어휘 등)>"
      }}
    }},
    {{
      "question_id": 2,
      "correct_choice": "<(A), (B), (C), (D) 중 정답>",
      "explanation": {{
        "main": "<정답에 대한 상세한 해설>",
        "distractors": "<오답 선택지에 대한 간략한 설명>",
        "learning_point": "<문제와 관련된 추가 학습 포인트 (문법, 어휘 등)>"
      }}
    }}
  ]
}}
```
"""

def get_prompt(prompt_type):
    """
    요청된 유형에 맞는 프롬프트 템플릿을 반환합니다.

    Args:
        prompt_type (str): "passage", "question", "answer" 중 하나

    Returns:
        str: 해당 프롬프트 템플릿 문자열
    """
    if prompt_type == "passage":
        return PASSAGE_GENERATION_PROMPT
    elif prompt_type == "question":
        return QUESTION_GENERATION_PROMPT
    elif prompt_type == "answer":
        return ANSWER_GENERATION_PROMPT
    else:
        raise ValueError(f"'{prompt_type}'은(는) 유효한 프롬프트 유형이 아닙니다.")

def format_prompt(prompt_type, **kwargs):
    """
    지정된 프롬프트 템플릿에 값을 채워서 반환합니다.
    
    Args:
        prompt_type (str): "passage", "question", "answer" 중 하나
        **kwargs: 프롬프트에 채울 값들
    
    Returns:
        str: 내용이 채워진 완성된 프롬프트
    """
    template = get_prompt(prompt_type)
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        print(f"프롬프트 포맷팅 오류: {e} 키가 누락되었습니다.")
        # 누락된 키가 있어도 일단 템플릿을 반환하여 디버깅을 돕습니다.
        return template
