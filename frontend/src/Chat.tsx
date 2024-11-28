import React, { useState } from "react";

interface Message {
  role: string;
  content: string;
}

interface ChatProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}

const Chat: React.FC<ChatProps> = ({ messages, setMessages }) => {
  const [input, setInput] = useState("");

  const handleSend = async () => {
    if (input.trim() === "") return;

    // 사용자 메시지 추가
    const userMessage: Message = { role: "user", content: input };
    setMessages((prevMessages) => [...prevMessages, userMessage]);

    // AI와 연결하기 위해 백엔드로 메시지를 전송
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            messages: [...messages, userMessage], // 기존 메시지 히스토리와 새로운 메시지 포함
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch AI response: ${response.status}`);
      }

      const data = await response.json();

      // AI 응답 추가
      const aiResponse: Message = { role: "assistant", content: data.response };
      setMessages((prevMessages) => [...prevMessages, aiResponse]);
    } catch (error) {
      console.error("Error fetching AI response:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "AI 응답을 불러오는 데 실패했습니다. 다시 시도해주세요.",
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }

    // 입력 필드 초기화
    setInput("");
  };

  return (
    <div className="w-full max-w-lg bg-white rounded shadow-lg p-4 flex flex-col space-y-4 h-screen max-h-screen">
      {/* 메시지 출력 영역 */}
      <div className="flex-1 overflow-y-auto p-2 border rounded">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`p-2 my-2 rounded ${
              msg.role === "user"
                ? "bg-blue-500 text-white self-end"
                : "bg-gray-200 self-start"
            }`}
          >
            {msg.content} {/* 채팅창 들어가자마자 프롬프트 출력되는 곳 */}
          </div>
        ))}
      </div>

      {/* 입력 필드 및 전송 버튼 */}
      <div className="flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 p-2 border rounded focus:outline-none focus:ring"
          placeholder="Type your message..."
        />
        <button
          onClick={handleSend}
          className="p-2 bg-blue-500 text-white rounded"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;
