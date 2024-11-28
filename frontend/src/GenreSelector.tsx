import React from "react";

interface GenreSelectorProps {
  onPromptReceived: (prompt: string, genre: string) => void;
}

const GenreSelector: React.FC<GenreSelectorProps> = ({ onPromptReceived }) => {
  const genres = ["survival", "mystery", "simulation", "romance"];

  // 프론트엔드에서 요청 보내기 (GenreSelector.tsx)
  const handleGenreSelect = async (genre: string) => {
    try {
      const response = await fetch("http://localhost:8000/get-prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ genre }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch prompt: ${response.status}`);
      }

      const data = await response.json();
      const prompt = data.prompt;

      const generateResponse = await fetch(
        "http://localhost:8000/generate-world",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ genre, prompt }),
        }
      );

      if (!generateResponse.ok) {
        throw new Error(`Failed to generate world: ${generateResponse.status}`);
      }

      const generatedData = await generateResponse.json();
      onPromptReceived(generatedData.content, genre);
    } catch (error) {
      console.error("Error fetching prompt or generating world:", error);
      onPromptReceived("프롬프트를 불러오는 데 실패했습니다.", genre);
    }
  };

  return (
    <div className="flex flex-col items-center space-y-2">
      <h2 className="text-xl font-bold">장르를 선택하세요:</h2>
      <div className="flex space-x-2">
        {genres.map((genre) => (
          <button
            key={genre}
            onClick={() => handleGenreSelect(genre)}
            className="p-2 bg-gray-200 hover:bg-gray-300 rounded"
          >
            {genre.toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  );
};

export default GenreSelector;
