from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import openai
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


app = FastAPI()

# CORS 설정
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

class PromptRequest(BaseModel):
    genre: str
    prompt: str

# 장르 기반 랜덤 프롬프트 선택 함수
def get_random_prompt(genre: str) -> str:

    genre_path = os.path.join("prompts", genre)  # 상위 장르 폴더 경로

    if not os.path.exists(genre_path):
        raise HTTPException(status_code=404, detail=f"Genre folder '{genre}' not found.")

    # 해당 장르 폴더의 모든 파일 검색
    txt_files = [f for f in os.listdir(genre_path) if f.endswith(".txt")]

    if not txt_files:
        raise HTTPException(status_code=404, detail=f"No prompt files found in genre '{genre}'.")

    # 랜덤으로 하나 선택
    random_file = random.choice(txt_files)
    file_path = os.path.join(genre_path, random_file)

    # 파일 내용 읽기
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


# ChatGPT API 호출 엔드포인트
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    프론트엔드에서 받은 메시지를 OpenAI ChatGPT API로 전달하고 응답을 반환합니다.
    """
    try:
        print(f"[DEBUG] Received chat request: {request}")
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages
        )
        response_content = completion.choices[0].message["content"]
        print(f"[DEBUG] AI Response: {response_content}")
        return ChatResponse(response=completion.choices[0].message["content"])
    except Exception as e:
        print(f"[ERROR] Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 랜덤 프롬프트 제공 엔드포인트
from fastapi import Request

@app.post("/get-prompt")
async def get_prompt(request: GenreRequest):
    try:
        print(f"Received request data: {request}")  # 디버깅 로그
        prompt = get_random_prompt(request.genre)
        print(f"세부 장르 프롬프트: {prompt}")  # 디버깅 로그
        return {"prompt": prompt}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-world")
async def generate_world(request: PromptRequest):
    """
    장르와 프롬프트를 바탕으로 새로운 게임 세계관을 생성합니다.
    """
    try:
        # 프롬프트 설정
        prompts = (
            f"지금 '{request.genre}', '{request.prompt}' 이 장르에 맞는 내용의 게임 세계관을 만들어줘야 해. "
            "한글로 말하고, 한 번 말할 때마다 200자 이내로 말하면 돼.반드시 200자일 필요는 없어 "
            "선택지 외의 답변을 해도 된다고 해줘. "
            "계속 이어서 스토리를 만들어줘. "
            "스토리가 갑자기 다른 이야기로 가거나 하면 안돼."
            "마지막엔 1인칭 시점의 대화형식으로 끝맺어야해 "
            "1인칭 시점의 상황에 대한 간단한 설명으로 시작되고"
            "사용자의 응답에 따라 이야기가 전개된다"
            "시스템은 3가지의 선택지를 제시하고 사용자가 선택한다"
            "사용자의 선택에 따라 시스템은 생존 확률을 퍼센트로 표시한다."
        )
        print(f"AI 프롬프트 받아오고 있니..: {prompts}")    

        # ChatGPT 호출
        completion = openai.ChatCompletion.create(
            model="gpt-4",  # 모델 선택
            messages=[{"role": "user", "content": prompts}],
        )

        print(f"[DEBUG] AI response received: {completion}")
        
        generated_content = completion.choices[0].message["content"]

        print(f"[DEBUG] Generated content for world: {generated_content}")

        return {"content": generated_content}
    
    except Exception as e:
        print(f"Error generating world: {e}")
        raise HTTPException(status_code=500, detail=str(e))
