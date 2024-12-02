from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import random
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.tools import Tool

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# LangChain 구성
llm = OpenAI(model_name="gpt-4", openai_api_key=openai_api_key)
memory = ConversationBufferMemory()

# 대화 체인 (히스토리 유지)
conversation_chain = ConversationChain(llm=llm, memory=memory)

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




# 장르별 랜덤 프롬프트 선택 함수

def get_random_prompt_tool(genre: str) -> str:
    print(f'genre: {genre}')
    genre_path = os.path.join(PROMPT_BASE_PATH, genre)  # 절대 경로 사용
    print(f"[DEBUG] Looking for prompts in: {genre_path}")

    # 폴더가 존재하지 않을 경우 예외 발생
    if not os.path.exists(genre_path):
        print(f"[ERROR] Genre folder not found: {genre_path}")
        raise HTTPException(status_code=404, detail=f"Genre folder '{genre}' not found.")
    print(f'장르 선택 됐니?: {genre}')
    
    # 해당 폴더 내 모든 텍스트 파일 검색
    txt_files = [f for f in os.listdir(genre_path) if f.endswith(".txt")]
    print(f"[DEBUG] Found files: {txt_files}")

    # 텍스트 파일이 없을 경우 예외 발생
    if not txt_files:
        print(f"[ERROR] No prompt files in folder: {genre_path}")
        raise HTTPException(status_code=404, detail=f"No prompt files found in genre folder '{genre}'.")

    # 랜덤으로 하나의 파일 선택
    random_file = random.choice(txt_files)
    file_path = os.path.join(genre_path, random_file)
    print(f"[DEBUG] Selected file: {random_file}")

    # 파일 읽기
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        print(f"[DEBUG] File content read successfully: {content[:50]}...")  # 처음 50자만 출력
        return content
    except Exception as e:
        print(f"[ERROR] Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {random_file}")



prompt_tool = Tool(
    name="RandomPrompt",
    func=get_random_prompt_tool,
    description="Retrieve a random prompt for the given genre."
)

# 엔드포인트 정의
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    대화 메시지를 처리하여 응답을 반환합니다.
    """
    try:
        print(f"[DEBUG] Received chat request: {request.messages}")
        user_message = request.messages[-1].content  # 마지막 메시지
        print(f"[DEBUG] User message: {user_message}")

        # LangChain ConversationChain 실행
        response = conversation_chain.run(user_message)
        print(f"[DEBUG] LangChain response: {response}")

        return ChatResponse(response=response)
    except Exception as e:
        print(f"[ERROR] Error in /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get-prompt")
async def get_prompt(request: GenreRequest):
    genre = request.genre
    # 유효한 폴더 경로 계산
    genre_path = os.path.join(PROMPT_BASE_PATH, genre)
    print(f"[DEBUG] Looking for prompts in: {genre_path}")

    # 폴더가 존재하지 않을 경우 예외 발생
    if not os.path.exists(genre_path):
        print(f"[ERROR] Genre folder not found: {genre_path}")
        raise HTTPException(status_code=404, detail=f"Genre folder '{genre}' not found.")

    # 텍스트 파일 검색
    txt_files = [f for f in os.listdir(genre_path) if f.endswith(".txt")]
    if not txt_files:
        print(f"[ERROR] No prompt files found in folder: {genre_path}")
        raise HTTPException(status_code=404, detail=f"No prompt files found in genre folder '{genre}'.")

    # 랜덤 파일 선택
    random_file = random.choice(txt_files)
    file_path = os.path.join(genre_path, random_file)
    print(f"[DEBUG] Selected file: {file_path}")

    # 파일 내용 읽기
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"genre": genre, "prompt": content}
    except Exception as e:
        print(f"[ERROR] Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {random_file}")
    
@app.post("/generate-world")
async def generate_world(request: GenreRequest):
    print(f"[DEBUG] Received genre: {request.genre}")
    genre = request.genre

    # genre에 따른 프롬프트 생성 또는 불러오기
    genre_path = os.path.join(PROMPT_BASE_PATH, genre)
    if not os.path.exists(genre_path):
        raise HTTPException(status_code=404, detail=f"Genre folder '{genre}' not found.")
    
    # 랜덤 프롬프트 파일 선택
    txt_files = [f for f in os.listdir(genre_path) if f.endswith(".txt")]
    if not txt_files:
        raise HTTPException(status_code=404, detail=f"No prompt files found for genre '{genre}'.")

    random_file = random.choice(txt_files)
    file_path = os.path.join(genre_path, random_file)

    # 프롬프트 내용 읽기
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            prompt = file.read()
        print(f"[DEBUG] Selected prompt: {prompt[:50]}...")  # 첫 50자 출력
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read prompt file for genre '{genre}'.")

    # 처리 로직 실행
    try:
        response_content = chain.invoke({"genre": genre, "prompt": prompt})
        print(f"[DEBUG] Generated content: {response_content[:50]}...")  # 첫 50자 출력
        return {"content": response_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate world.")
