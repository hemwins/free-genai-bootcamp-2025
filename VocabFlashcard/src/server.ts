import express from "express";
import cors from "cors";
import { Request, Response } from "express";

const app = express();
const port = 8083;

// Update CORS configuration to allow external calls
app.use(
  cors({
    origin: ["http://localhost:8082", "http://localhost:4999", "http://localhost:5173"], // Add any other allowed origins
    methods: ["GET", "POST"],
    credentials: true,
  })
);
app.use(express.json());

app.get("/get_word", async (req: Request, res: Response) => {
  const group_id = req.query.group_id as string;
  try {
    const response = await fetch(
      `http://localhost:4999/api/groups/${group_id}/words/raw`
    );
    const vocabulary = await response.json();
    if (vocabulary && vocabulary.length > 0) {
      const randomIndex = Math.floor(Math.random() * vocabulary.length);
      const randomWord = vocabulary[randomIndex];
      res.json(randomWord);
    } else {
      res.status(404).json({ error: "No words available" });
    }
  } catch (error) {
    res.status(500).json({ error: "API error" });
  }
});

app.post("/check_answer", async (req: Request, res: Response) => {
  const { answer, kanji, romaji, word_id } = req.body;
  const session_id = req.query.session_id as string;
  const correct =
    answer.trim() === kanji.trim() || answer.trim() === romaji.trim();

  const updateBackend = async () => {
    try {
      await fetch(
        `http://localhost:4999/api/study-sessions/${session_id}/review`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ word_id, correct }),
        }
      );
    } catch (error) {
      console.error("Error updating backend. Retrying...", error);
      setTimeout(updateBackend, 2000); // Retry after 2 seconds
    }
  };

  updateBackend(); // Send data to backend without blocking frontend response

  res.json({
    result: correct ? "Correct! Well done! 🎉" : "Try again! Keep going! 💪",
    status: correct ? "learned" : "retry",
    correct,
  });
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
