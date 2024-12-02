from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import random
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# FastAPI 앱 설정
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일의 디렉토리 경로
PROMPT_BASE_PATH = os.path.join(BASE_DIR, "prompts")  # prompts 폴더 절대 경로

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LangChain 구성
llm = ChatOpenAI(temperature=0.4, model="gpt-4", openai_api_key=openai_api_key)
memory = ConversationBufferMemory(return_messages=True)

# 히스토리 함수 정의
def get_session_history(session_id: str):
    return memory.chat_memory.messages

# RunnableWithMessageHistory 초기화
conversation_chain = RunnableWithMessageHistory(
    runnable=llm,
    get_session_history=get_session_history
)

# 단일 프롬프트 체인 (세계관 생성 등 단일 작업에 사용)
prompt_template = PromptTemplate(
    input_variables=["genre", "prompt"],
    template=(
        "지금 '{genre}', '{prompt}' 이 장르에 맞는 내용의 게임 세계관을 만들어줘야 해. "
        "한글로 말하고, 한 번 말할 때마다 200자 이내로 말하면 돼."
        "선택지 외의 답변을 해도 된다고 해줘. "
        "계속 이어서 스토리를 만들어줘. "
        "스토리가 갑자기 다른 이야기로 가거나 하면 안돼."
        "마지막엔 1인칭 시점의 대화형식으로 끝맺어야해 "
        "1인칭 시점의 상황에 대한 간단한 설명으로 시작되고"
        "사용자의 응답에 따라 이야기가 전개된다"
        "시스템은 3가지의 선택지를 제시하고 사용자가 선택한다"
        "사용자의 선택에 따라 시스템은 생존 확률을 퍼센트로 표시한다."
    )
)
chain = LLMChain(llm=llm, prompt=prompt_template)

# Request/Response 모델 정의
class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    response: str

class GenreRequest(BaseModel):
    genre: str

class GenerateWorldRequest(BaseModel):
    genre: str
    prompt: str

# 프롬프트 파일 읽기 함수 통합
def read_random_prompt(genre: str) -> str:
    genre_path = os.path.join(PROMPT_BASE_PATH, genre)

    if not os.path.exists(genre_path):
        raise HTTPException(status_code=404, detail=f"Genre folder '{genre}' not found.")

    txt_files = [f for f in os.listdir(genre_path) if f.endswith(".txt")]
    if not txt_files:
        raise HTTPException(status_code=404, detail=f"No prompt files found in genre folder '{genre}'.")

    random_file = random.choice(txt_files)
    file_path = os.path.join(genre_path, random_file)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read prompt file: {e}")

# 엔드포인트 정의
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    대화 메시지를 처리하여 응답을 반환합니다.
    """
    try:
        user_message = request.messages[-1].content  # 마지막 메시지
        response = conversation_chain.invoke({"session_id": "session_id", "input": user_message})
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in /chat: {e}")

@app.post("/get-prompt")
async def get_prompt(request: GenreRequest):
    """
    장르별 랜덤 프롬프트를 반환합니다.
    """
    try:
        content = read_random_prompt(request.genre)
        return {"genre": request.genre, "prompt": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-world")
async def generate_world(request: GenerateWorldRequest):
    """
    장르와 프롬프트를 기반으로 새로운 게임 세계관을 생성합니다.
    """
    try:
        response_content = chain.run({"genre": request.genre, "prompt": request.prompt})
        return {"content": response_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain invocation failed: {e}")
