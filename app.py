import streamlit as st
import openai
import time

# 페이지 설정
st.set_page_config(page_title="AI 챗봇", page_icon="🤖")

# 제목
st.title("🤖 AI 챗봇")

# API 키 입력
api_key = st.sidebar.text_input("OpenAI API Key를 입력하세요", type="password")

# 파일 업로드
uploaded_file = st.sidebar.file_uploader(
    "설문지 데이터 파일 업로드", 
    type=['csv', 'txt', 'json', 'xlsx'],
    help="CSV, TXT, JSON, XLSX 파일을 업로드하세요"
)

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

if "uploaded_file_id" not in st.session_state:
    st.session_state.uploaded_file_id = None

# 파일 업로드 처리
if uploaded_file and st.session_state.uploaded_file_id is None:
    try:
        # Streamlit 파일 객체를 바이트로 변환
        file_content = uploaded_file.read()
        uploaded_file.seek(0)  # 파일 포인터 리셋
        
        # 파일을 OpenAI에 업로드
        file_response = client.files.create(
            file=(uploaded_file.name, file_content),
            purpose='assistants'
        )
        st.session_state.uploaded_file_id = file_response.id
        
        # 벡터 스토어 생성 및 파일 추가
        vector_store = client.beta.vector_stores.create(
            name="설문지 데이터"
        )
        
        client.beta.vector_stores.files.create(
            vector_store_id=vector_store.id,
            file_id=file_response.id
        )
        
        # Assistant에 벡터 스토어 연결
        client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store.id]
                }
            }
        )
        
        st.sidebar.success(f"파일 업로드 완료: {uploaded_file.name}")
        
    except Exception as e:
        st.sidebar.error(f"파일 업로드 실패: {str(e)}")
        st.sidebar.error(f"자세한 오류: {type(e).__name__}")

# 업로드된 파일 정보 표시
if st.session_state.uploaded_file_id:
    st.sidebar.info("📄 데이터 파일이 로드되었습니다")

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
st.sidebar.markdown("2. 설문지 데이터 파일을 업로드하세요")
st.sidebar.markdown("3. 아래 채팅창에 메시지를 입력하세요")
st.sidebar.markdown("4. AI가 데이터를 기반으로 답변해드립니다!")

# 대화 초기화 버튼
if st.sidebar.button("대화 초기화"):
    st.session_state.messages = []
    # 새 스레드 생성
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.rerun()

# 파일 삭제 버튼
if st.session_state.uploaded_file_id and st.sidebar.button("업로드된 파일 삭제"):
    try:
        client.files.delete(st.session_state.uploaded_file_id)
        st.session_state.uploaded_file_id = None
        st.sidebar.success("파일이 삭제되었습니다")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"파일 삭제 실패: {str(e)}")
