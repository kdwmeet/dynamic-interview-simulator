import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="동적 AI 모의 면접관", layout="wide")
st.title("동적 AI 모의 면접관")
st.markdown("입력된 이력서와 직무 설명서를 바탕으로 실시간 꼬리 질문을 생성하는 턴제 모의 면접 파이프라인입니다.")
st.divider()

# 세션 관리
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "interview_001"
if"interview_started" not in st.session_state:
    st.session_state.interview_started = False

config = {"configurable": {"thread_id": st.session_state.thread_id}}

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("면접 설정")
    with st.form("setup_form"):
        resume_input = st.text_area("지원자 이력서 요약", height=150, placeholder="예: 파이썬 웹 개발 3년차, Django 및 LangGraph 활용 경험 보유...")
        job_desc_input = st.text_area("지원 직무 설명서(JD)", height=150, placeholder="예: 백엔드 엔지니어 (AI 에이전트 파이프라인 구축 및 서버 아키텍처 설계)")
        max_turns_input = st.number_input("진행할 면접 질문 횟수 (턴)", min_value=1, max_value=10, value=3)

        start_btn = st.form_submit_button("모의 면접 시작", use_container_width=True)

with col2:
    st.subheader("면접 대화 기록")

    # 면접 시작 버튼 클릭 시 초기화
    if start_btn and resume_input.strip() and job_desc_input.strip():
        st.session_state.thread_id = f"thread_{st.session_state.thread_id}_new"
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        st.session_state.interview_started = True

        initial_state = {
            "resume": resume_input,
            "job_desc": job_desc_input,
            "chat_history": [],
            "current_question": "",
            "user_answer": "",
            "turn_count": 0,
            "max_turns": max_turns_input,
            "feedback_report": ""
        }

        with st.spinner("면접관이 이력서를 검토하고 첫 질문을 준비 중..."):
            for output in app_graph.stream(initial_state, config):
                if not output:
                    continue

    # 인터뷰가 진행 중일 때 UI 렌더링
    if st.session_state.interview_started:
        graph_state = app_graph.get_state(config)
        current_state_dict = graph_state.values if graph_state else {}

        chat_history = current_state_dict.get("chat_history", [])

        # 이전 대화 기록 화면에 출력
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            if role == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(content)
            
            else:
                with st.chat_message("user"):
                    st.markdown(content)
        
        # 현재 일시정지 상태인지 확인 후 사용자 입력 폼 제공
        if graph_state and graph_state.next and "receive_answer" in graph_state.next:
            user_input = st.chat_input("면접관의 질문에 답변하십시오.")
            if user_input:
                # 사용자가 입력한 답변을 UI에 즉시 반영
                with st.chat_message("user"):
                    st.markdown(user_input)

                # 상태 업데이트 후 파이프라인 재개
                app_graph.update_state(config, {"user_answer": user_input})

                with st.spinner("답변을 분석하고 다음 질문을 준비 중..."):
                    for output in app_graph.stream(None, config):
                        if not output:
                            continue
                
                st.rerun()
        
        # 면접이 모두 종료되어 평가 리포트가 생성되었는지 확인
        feedback = current_state_dict.get("feedback_report", "")
        if feedback:
            st.success("면접이 모두 종료되었습니다. 아래에서 최종 평가 리포트를 확인하십시오.")
            with st.expander("면접관의 최종 평가 리포트", expanded=True):
                st.markdown(feedback)