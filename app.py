import streamlit as st
import openai
import time

# 페이지 설정
st.set_page_config(page_title="AI 챗봇", page_icon="🤖")

# 제목
st.title("🤖 AI 챗봇")

# API 키 입력
api_key = st.sidebar.text_input("OpenAI API Key를 입력하세요", type="password")

if not api_key:
    st.warning("왼쪽 사이드바에 API Key를 입력해주세요!")
    st.stop()

# OpenAI 클라이언트 설정
client = openai.OpenAI(api_key=api_key)

# Assistant ID
ASSISTANT_ID = "asst_pz6WD4z3sdtOrJz4JC8BT1Kk"

# 세션 상태 초기화
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 어시스턴트 응답
    with st.chat_message("assistant"):
        try:
            # 메시지를 스레드에 추가
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=prompt
            )
            
            # 어시스턴트 실행
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID
            )
            
            # 실행 완료까지 대기
            with st.spinner("답변을 생성하고 있습니다..."):
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
            
            if run.status == "completed":
                # 최신 메시지 가져오기
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                
                # 어시스턴트의 최신 응답 가져오기
                assistant_message = messages.data[0].content[0].text.value
                st.markdown(assistant_message)
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            else:
                st.error(f"오류가 발생했습니다: {run.status}")
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

# 사이드바에 정보 표시
st.sidebar.markdown("---")
st.sidebar.markdown("### 사용법")
st.sidebar.markdown("1. OpenAI API Key를 입력하세요")
st.sidebar.markdown("2. 아래 채팅창에 메시지를 입력하세요")
st.sidebar.markdown("3. AI가 답변해드립니다!")

# 대화 초기화 버튼
if st.sidebar.button("대화 초기화"):
    st.session_state.messages = []
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.rerun()