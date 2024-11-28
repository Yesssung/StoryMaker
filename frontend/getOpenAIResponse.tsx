import axios from "axios";

const getOpenAIResponse = async (prompt) => {
  try {
    const response = await axios.post("http://localhost:8000/chat/", {
      prompt: prompt,
      max_tokens: 100,
      model: "text-davinci-003",
    });

    console.log("Response:", response.data.response);
    return response.data.response;
  } catch (error) {
    console.error("Error:", error);
  }
};
