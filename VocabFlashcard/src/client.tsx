import React, { useState, useEffect } from "react";
import styles from "./App.module.css";
import { logger } from "./utils/logger";
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from "@mui/material/Typography/Typography";

interface Word {
  english: string;
  kanji: string;
  romaji: string;
  id: string;
}

interface CheckAnswerResponse {
  result: string;
  correct: boolean;
  status: "learned" | "retry";
}
const card = (
  <React.Fragment>
    <CardContent>
      <Typography gutterBottom sx={{ color: 'text.secondary', fontSize: 14 }}>
        Word of the Day
      </Typography>
      <Typography variant="h5" component="div">
        belent
      </Typography>
      <Typography sx={{ color: 'text.secondary', mb: 1.5 }}>adjective</Typography>
      <Typography variant="body2">
        well meaning and kindly.
        <br />
        {'"a benevolent smile"'}
      </Typography>
    </CardContent>
    {/* <CardActions>
      <Button size="small">Learn More</Button>
    </CardActions> */}
  </React.Fragment>
);

const App: React.FC = () => {
  const [word, setWord] = useState<Word | null>(null);
  const [options, setOptions] = useState<string[]>([]);
  const [result, setResult] = useState("");
  const [showKanji, setShowKanji] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showContinueButtons, setShowContinueButtons] = useState(false);
  const [goodbyeMessage, setGoodbyeMessage] = useState("");

  const params = new URLSearchParams(window.location.search);
  const group_id = params.get("group_id");
  const session_id = params.get("session_id");

  const fetchWord = async () => {
    setIsLoading(true);
    setError(null);
    logger.info(`Fetching words for group_id: ${group_id}`);

    try {
      const response = await fetch(`/api/get_word?group_id=${group_id}`);
      const data = await response.json();
      setWord(data.word);

      // Shuffle correct and wrong Kanji together
      const shuffledOptions = [data.word.kanji, ...data.wrongKanjiOptions].sort(
        () => Math.random() - 0.5
      );
      setOptions(shuffledOptions);

      setShowKanji(false);
    } catch (error) {
      logger.error(`Error fetching words: ${error}`);
      setError("Failed to fetch words. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const checkAnswer = async (selectedKanji: string) => {
    if (!word) return;
    logger.info(
      `Checking answer for word_id: ${word.id}, session_id: ${session_id}`
    );

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/check_answer?session_id=${session_id}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            answer: selectedKanji,
            kanji: word.kanji,
            romaji: word.romaji,
            word_id: word.id,
          }),
        }
      );

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      const data: CheckAnswerResponse = await response.json();
      setResult(data.result);
      logger.info(
        `Answer check result: ${data.correct ? "correct" : "incorrect"}`
      );

      if (data.correct) {
        setShowContinueButtons(true);
      }
    } catch (error) {
      logger.error(`Error checking answer: ${error}`);
      setError("Failed to check answer. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    setShowContinueButtons(false);
    fetchWord();
    setResult(""); // Clear the result message
  };

  const handleQuit = () => {
    setShowContinueButtons(false);
    setGoodbyeMessage("Goodbye! Thanks for practicing!");
  };

  useEffect(() => {
    fetchWord();
  }, []);

  if (error) {
    return (
      <div className={styles.app}>
        <div className={styles.errorMessage}>
          {error}
          <button className={styles.button} onClick={() => fetchWord()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.app}>
      <header className={styles.appHeader}>
        <h1>Vocab Flashcard</h1>
        {isLoading ? (
          <div>Loading...</div>
        ) : (
          word &&
          !goodbyeMessage && (
            <div className={styles.wordContainer}>
              {/* Main Flashcard - Shows English */}
              <p
                className={styles.mainFlashcard}
                onClick={() => setShowKanji(!showKanji)}
              >
                English: {word.english}
              </p>

              {/* Four Kanji Option Flashcards */}
              <div className={styles.optionsContainer}>
                {options.map((option, index) => (
                  <div
                    key={index}
                    className={styles.optionFlashcard}
                    onClick={() => checkAnswer(option)}
                  >
                    {option}
                  </div>
                ))}
              </div>

              <p>{result}</p>
            </div>
          )
        )}
      </header>
      {showContinueButtons && (
        <div className={styles.continueButtons}>
          <button className={styles.button} onClick={handleContinue}>
            Continue
          </button>
          <button className={styles.button} onClick={handleQuit}>
            Quit
          </button>
        </div>
      )}
      {goodbyeMessage && (
        <div className={styles.goodbyeMessage}>{goodbyeMessage}</div>
      )}
    </div>
  );
};

export default App;
