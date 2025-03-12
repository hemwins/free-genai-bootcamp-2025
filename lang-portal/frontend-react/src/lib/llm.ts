import Groq from 'groq-sdk';
//import dotenv from 'dotenv';

//dotenv.config();
// Initialize Groq client
const groq = new Groq({
  apiKey: import.meta.env.VITE_GROQ_API_KEY,
  dangerouslyAllowBrowser: true
});

export async function generateVocabularyFromLLM(category: string) {
  const prompt = `Generate a structured JSON output for Japanese vocabulary related to the theme "${category}". The output should be an array of objects, where each object represents a vocabulary item with the following structure:
  {
    "kanji": "Japanese word in kanji or kana",
    "romaji": "Romanized version of the word",
    "english": "English translation",
    "parts": [
      {
        "kanji": "Individual kanji or kana character",
        "romaji": ["Possible readings of the character"]
      },
      ...
    ]
  }
  Generate exactly 5 vocabulary items and send back raw json and nothing else.

  Here is an example of bad output:
  {
    "kanji": "晴れ",
    "romaji": "hare",
    "english": "sunny",
    "parts": [
      {
        "kanji": "晴",
        "romaji": [
          "seki",
          "haru"
        ]
  ...
  }
  ^ The reason this is bad is because the parts of romaji that are shown do not represent the word. 
  Instead of listing out seki haru, it should just say ha because that is what the kanji is representing 
  for that word hare.

  Another reason this is bad is because it's missing the other part. 
  There should be 2 parts: one for ha and the other for re.

  Here are great examples with all of the parts broken up:
  {
    "kanji": "古い",
    "romaji": "furui",
    "english": "old",
    "parts": [
      { "kanji": "古", "romaji": ["fu", "ru"] },
      { "kanji": "い", "romaji": ["i"] }
    ]
  },
  {
    "kanji": "忙しい",
    "romaji": "isogashii",
    "english": "busy",
    "parts": [
      { "kanji": "忙", "romaji": ["i","so","ga"] },
      { "kanji": "し", "romaji": ["shi"] },
      { "kanji": "い", "romaji": ["i"] }
    ]
  },
  {
    "kanji": "新しい",
    "romaji": "atarashii",
    "english": "new",
    "parts": [
      { "kanji": "新", "romaji": ["a","ta","ra"] },
      { "kanji": "し", "romaji": ["shi"] },
      { "kanji": "い", "romaji": ["i"] }
    ]
  },
  {
    "kanji": "悪い",
    "romaji": "warui",
    "english": "bad",
    "parts": [
      { "kanji": "悪", "romaji": ["wa","ru"] },
      { "kanji": "い", "romaji": ["i"] }
    ]
  }

  ^ This is a good output because the word represents all the kanji and kana shown in the word.
  
  `;

  try {
    const completion = await groq.chat.completions.create({
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
      model: 'gemma2-9b-it',
      temperature: 0.7,
      max_tokens: 1000,
    });

    console.log("===========================");
    console.log("response", completion.choices[0].message.content);
    console.log("===========================");

    // Parse the generated text as JSON
    const vocabularyData = JSON.parse(completion.choices[0].message.content || '[]');
    return vocabularyData;
  } catch (error) {
    console.error("Error generating vocabulary from LLM:", error);
    throw error;
  }
}
