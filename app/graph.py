from typing import TypedDict, List, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# 상태 정의
class InterviewState(TypedDict):
    resume: str
    job_desc: str
    chat_history: List[Dict[str, str]]
    current_question: str
    user_answer: str
    turn_count: int 
    max_turns: int
    feedback_report: str

# 노드 구현
def ask_question_node(state: InterviewState):
    """이력서와 이전 답변을 바탕으로 ㅁ녀접 질문(또는 꼬리 질문)을 생성"""
    llm = ChatOpenAI(model="gpt-5.4-nano", reasoning_effort="high")
    resume = state.get("resume", "")
    job_desc = state.get("job_desc", "")
    chat_history = state.get("chat_history", [])

    # 프롬프트 주입용 텍스트 조립 
    history_str = ""
    for msg in chat_history:
        role = "면접관" if msg.get("role") == "assistant" else "지원자"
        content = msg.get("content", "")
        history_str += role + ": " + content + "\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 전문 면접관입니다. 지원자의 이력서와 직무 설명서를 바탕으로 면접 질문을 던집니다. 이전 대화 기록이 있다면 지원자의 답변을 분석하여 예리한 꼬리 질문을 던지십시오. 한 번에 오직 하나의 질문만 출력해야 합니다."),
        ("user", "이력서:\n{resume}\n\n직무 설명서:\n{job_desc}\n\n대화 기록:\n{history_str}\n\n다음 면접 질문을 작성하십시오.")
    ])

    response = (prompt | llm).invoke({
        "resume": resume,
        "job_desc": job_desc,
        "history_str": history_str
    })

    question = response.content
    new_history = chat_history + [{"role": "assistant", "content": question}]

    return {"current_question": question, "chat_history": new_history}

def receive_answer_node(state: InterviewState):
    """일시 정지 후 전달받은 사용자의 답변을 상태에 기록"""
    user_answer = state.get("user_answer", "")
    chat_history = state.get("chat_history", [])
    turn_count = state.get("turn_count", 0)

    new_history = chat_history + [{"role": "user", "content": user_answer}]

    return {"chat_history": new_history, "turn_count": turn_count + 1}

def evaluate_node(state: InterviewState):
    """지정된 면접 횟수가 끝나면 전체 대화를 분석하여 피드백을 제공"""
    llm = ChatOpenAI(model="gpt-5.4-nano", reasoning_effort="high")
    resume = state.get("resume", "")
    job_desc = state.get("job_desc", "")
    chat_history = state.get("chat_history", [])

    history_str = ""
    for msg in chat_history:
        role = "면접관" if msg.get("role") == "assistant" else "지원자"
        content = msg.get("content", "")
        history_str += role + ": " + content + "\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 최종 평가 에이전트입니다. 지원자의 전체 면접 대화 기록을 분석하여 강점, 약점, 보완점, 그리고 직무 적합성을 다루는 상세한 피드백 리포트를 작성하십시오."),
        ("user", "이력서:\n{resume}\n\n직무 설명서:\n{job_desc}\n\n대화 기록:\n{history_str}\n\n최종 평가 리포트를 작성하십시오.")
    ])

    response = (prompt | llm).invoke({
        "resume": resume,
        "job_desc": job_desc,
        "history_str": history_str
    })

    return {"feedback_report": response.content}

# 라우팅 조건 함수
def route_next(state: InterviewState):
    """진행된 턴 수를 확인하여 다음 질문으로 갈지, 평가로 갈지 결정"""
    turn_count = state.get("turn_count", 0)
    max_turns = state.get("max_turns", 3)
    if turn_count >= max_turns:
        return "evaluate"
    return "ask_question"

# 그래프 조립 및 컴파일
workflow = StateGraph(InterviewState)
workflow.add_node("ask_question", ask_question_node)
workflow.add_node("receive_answer", receive_answer_node)
workflow.add_node("evaluate", evaluate_node) 

workflow.add_edge(START, "ask_question")
# 질문 작성 후 사용자의 답변을 받기 위해 연결
workflow.add_edge("ask_question", "receive_answer")
workflow.add_conditional_edges("receive_answer", route_next, {"ask_question": "ask_question", "evaluate": "evaluate"})
workflow.add_edge("evaluate", END)

# 체크포인터 연결 및 receive_answer 실행 직전 일시 정지 설정
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory, interrupt_before=["receive_answer"])