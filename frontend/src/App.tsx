import React, { useState } from "react";
import Chat from "./Chat";
import GenreSelector from "./GenreSelector";

interface Message {
  role: string;
  content: string;
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null);

  const handlePromptReceived = (prompt: string, genre: string) => {
    // 받아온 가공된 세계관 내용을 메시지로 추가
    setMessages([{ role: "assistant", content: prompt }]);
    setSelectedGenre(genre);
  };

  return (
    <div className="flex justify-center items-center h-screen bg-gray-100">
      {!selectedGenre ? (
        <GenreSelector onPromptReceived={handlePromptReceived} />
      ) : (
        <Chat messages={messages} setMessages={setMessages} />
      )}
    </div>
  );
};

export default App;
