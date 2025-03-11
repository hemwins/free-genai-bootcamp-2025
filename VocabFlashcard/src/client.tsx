import React, { useState, useEffect } from "react";
import styles from "./App.module.css";
import { logger } from "./utils/logger";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography/Typography";
import Grid from "@mui/material/Grid2";
import { styled } from "@mui/material/styles";
import { createTheme, ThemeProvider } from "@mui/material/styles";

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
const theme = createTheme({
  palette: {
    primary: {
      main: '#000000',       // Black
      contrastText: '#FFFFFF', // White
    },
    secondary: {
      main: '#FFFFFF',       // White
      contrastText: '#000000', // Black
    },
  },
});
const card = (lang: string, word: string, isAlone: boolean = false) => (
  <React.Fragment>
    <CardContent sx={{ height: '100%', minWidth: { sm: 400 }, width: '100%' , textAlign: 'center' }}>
      <Typography gutterBottom sx={{ color: 'text.primary', fontSize: 14 }} >
        {lang} word is:
      </Typography>
      <Typography variant="h5" component="div">
        {word}
      </Typography>
    </CardContent>
  </React.Fragment>
);
const CustomPrimaryButton = styled(Button)(({ theme }) => ({
  color: theme.palette.primary.main,
  backgroundColor: theme.palette.primary.contrastText,
  '&:hover': {
    backgroundColor: theme.palette.primary.light,
  },
}));

const CustomSecondaryButton = styled(Button)(({ theme }) => ({
  color: theme.palette.secondary.main,
  backgroundColor: theme.palette.primary.main,
  border: `1px solid ${theme.palette.grey[500]}`,
  '&:hover': {
    backgroundColor: theme.palette.secondary.light,
  },
}));
const params = new URLSearchParams(window.location.search);
const group_id = params.get("group_id");
const session_id = params.get("session_id");

const App: React.FC = () => {
  const [word, setWord] = useState<Word | null>(null);
  const [options, setOptions] = useState<string[]>([]);
  const [result, setResult] = useState("");
  const [showKanji, setShowKanji] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showContinueButtons, setShowContinueButtons] = useState(false);
  const [goodbyeMessage, setGoodbyeMessage] = useState("");


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
          <Button className={styles.button} onClick={() => fetchWord()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <Typography variant="h4" color="white" align="center">
        Vocab Flashcard
      </Typography>
      {isLoading ? (
        <div>Loading...</div>
      ) : (
        word &&
        !goodbyeMessage && (
          <div className={styles.wordContainer}>
            <Grid container justifyContent="center" alignItems="center" spacing={2}>
              <Grid display="flex" justifyContent="center" alignItems="center" size={12}>
                <Card>{card("English", word.english, true)}</Card>
              </Grid>
              <Grid size={12}>
            <Typography variant="h6" color="white" align="center">
              Choose one from below options...
            </Typography>
            </Grid>
              {options.map((option, index) => (
                <Grid size={{ xs: 6, md: 6 }} display="flex" justifyContent="center" alignItems="center">
                  <Card key={index} onClick={() => checkAnswer(option)}>
                    {card("Kanji", option)}
                  </Card>
                </Grid>
              ))}
            <Grid size={12}>
            <Typography variant="h6" color="white" align="center">
              {result}
            </Typography>
            </Grid>
            </Grid>
          </div>
        )
      )}
      {showContinueButtons && (
        <Grid container spacing={2} justifyContent="center" alignItems="center">
          <Grid display="flex" justifyContent="center" alignItems="center" size={12}>
            <CustomPrimaryButton variant="contained" onClick={handleContinue}>
              Continue
            </CustomPrimaryButton>
          </Grid>
          <Grid display="flex" justifyContent="center" alignItems="center" size={12}>
            <CustomSecondaryButton
              variant="outlined"
              className={styles.button}
              onClick={handleQuit}
            >
              Quit
            </CustomSecondaryButton>
          </Grid>
        </Grid>
      )}
      {goodbyeMessage && (
        <Typography margin="normal" variant="h6" color="white" align="center">
          {goodbyeMessage}
        </Typography>
      )}
    </ThemeProvider>
  );
};

export default App;
