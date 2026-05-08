# Dynamic AI Interview Simulator (동적 AI 모의 면접관)

## 1. 프로젝트 개요

본 프로젝트는 정해진 질문만 던지는 정적인 챗봇 형태를 벗어나, LangGraph의 상태 유지(State Management) 기능과 실행 제어(Interrupt) 기능을 결합하여 구현한 턴제(Turn-based) AI 모의 면접관입니다.

지원자의 이력서와 직무 설명서(JD)를 기반으로 맞춤형 질문을 생성하며, 지원자의 실시간 답변을 분석하여 논리적 허점이나 구체적인 경험을 묻는 꼬리 질문을 동적으로 생성합니다. 설정된 턴 수가 종료되면 전체 대화를 평가하여 전문적인 피드백 리포트를 제공합니다.

## 2. 주요 기능

* 동적 꼬리 질문 생성: 이전 대화의 맥락(Context)을 완벽하게 기억하고, 사용자의 방금 전 답변에 기반한 심층 질문을 즉석에서 만들어냅니다.
* Human-in-the-Loop 대화 제어: 에이전트가 질문을 생성한 후 `interrupt_before` 속성을 통해 파이프라인을 일시 정지하고, 사용자의 채팅 입력이 완료되면 상태를 업데이트하여 안전하게 실행을 재개합니다.
* 종합 피드백 리포트: 단순 대화로 끝나지 않고, 면접 종료 후 별도의 평가 에이전트 노드가 개입하여 직무 적합성과 보완점을 정리한 최종 분석 결과를 제공합니다.

## 3. 기술 스택

* Language: Python 3.10+
* Package Manager: uv
* LLM: OpenAI gpt-5.4-nano (질문 생성 및 평가의 논리성을 위해 reasoning_effort="high" 적용)
* Orchestration: LangGraph (StateGraph, MemorySaver 기반 인터럽트 및 체크포인트 제어)
* Web Framework: Streamlit (실시간 채팅 인터페이스 구현)

## 4. 프로젝트 구조
```
dynamic-interview-simulator/
├── .env                  
├── requirements.txt      
├── main.py               
└── app/
    ├── __init__.py
    └── graph.py          
```
## 5. 설치 및 실행 가이드

### 5.1 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.
OPENAI_API_KEY=sk-your-api-key-here

### 5.2 의존성 설치 및 실행
uv venv
uv pip install -r requirements.txt
uv run streamlit run main.py

## 6. 실행 화면