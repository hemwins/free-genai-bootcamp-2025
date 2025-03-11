import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import express from "express";
import { logger } from "./src/utils/logger.js"; // Add .js extension for ESM
import type { Express, Request, Response, NextFunction } from "express"; // Add type imports

export default defineConfig({
  plugins: [
    react(),
    {
      name: "configure-server",
      configureServer(server) {
        server.middlewares.use(express.json());

        // Add logging middleware
        server.middlewares.use(async (req, res, next) => {
          //const timestamp = new Date().toISOString();
          console.info(`info: ${req.method} ${req.url}`);

          if (req.url?.startsWith("/api/")) {
            try {
              if (req.url.startsWith("/api/get_word")) {
                const group_id = new URL(
                  req.url,
                  "http://localhost"
                ).searchParams.get("group_id");
                console.info(`info: Fetching words for group_id: ${group_id}`);
                const response = await fetch(
                  `http://localhost:4999/api/groups/${group_id}/words/raw`
                );
                const vocabulary = await response.json();
                const wordsArray = vocabulary.words;
                console.info(`info: Fetched vocabulary: ${wordsArray}`);
                if (!wordsArray || wordsArray.length < 4) {
                  console.info(`Not enough words to generate options`);
                }

                if (!wordsArray || wordsArray.length === 0) {
                  console.error("No words found in API response");
                  return res.end(
                    JSON.stringify({ error: "No words available" })
                  );
                } else {
                  const randomWord =
                    wordsArray[Math.floor(Math.random() * wordsArray.length)];
                  // Get three wrong Kanji options
                  const wrongKanjiOptions = wordsArray
                    .filter((w) => w.kanji !== randomWord.kanji) // Exclude the correct one
                    .sort(() => Math.random() - 0.5) // Shuffle
                    .slice(0, 3) // Pick first 3 after shuffle
                    .map((w) => w.kanji); // Extract Kanji only
                  console.info(
                    `info: Random word: ${JSON.stringify(randomWord)}`
                  );
                  console.info(
                    `info: kanji word: ${JSON.stringify(wrongKanjiOptions)}`
                  );
                  return res.end(
                    JSON.stringify({
                      word: randomWord,
                      wrongKanjiOptions: wrongKanjiOptions,
                    })
                  );
                }
              }

              if (req.url.startsWith("/api/check_answer")) {
                const session_id = new URL(
                  req.url,
                  "http://localhost"
                ).searchParams.get("session_id");
                console.info(
                  `info: Checking answer for session_id: ${session_id}`
                );
                const body = req.body;
                const correct =
                  body.answer.trim() === body.kanji.trim() ||
                  body.answer.trim() === body.romaji.trim();
                console.info(`info: Correct value is: ${correct}`);
                await fetch(
                  `http://localhost:4999/api/study-sessions/${session_id}/review`,
                  {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ word_id: body.word_id, correct }),
                  }
                );

                return res.end(
                  JSON.stringify({
                    result: correct
                      ? "Correct! Well done! 🎉"
                      : "OOPs! Try again! Keep going! 💪",
                    status: correct ? "learned" : "retry",
                    correct,
                  })
                );
              }
            } catch (error) {
              console.error(`error: API error: ${error}`);
              console.error(error);
              res.statusCode = 500;
              return res.end(JSON.stringify({ error: "API error" }));
            }
          }
          next();
        });
      },
    },
  ],
  server: {
    port: 8083,
    strictPort: true,
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
  },
  css: {
    modules: {
      localsConvention: "camelCase",
    },
  },
});
