from groq import Groq
import os
from dotenv import load_dotenv
import json

load_dotenv(override=True)

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

def generate_vocabulary(category: str) -> dict:
    """Generate vocabulary using Groq LLM"""
    prompt = (
        f'Generate a structured JSON array for Japanese vocabulary related to "{category}". '
        'Each object should have this structure:\n'
        '{\n'
        ' "kanji": "Japanese word in kanji or kana",\n'
        ' "romaji": "Romanized version of the word",\n'
        ' "english": "English translation",\n'
        ' "parts": [\n'
        '    {\n'
        '        "kanji": "Individual kanji or kana character",\n'
        '        "romaji": ["Possible readings of the character"]\n'
        '    }\n'
        '   ]\n'
        '}\n\n'
        'Important rules:\n'
        '1. Generate exactly 5 items\n'
        '2. Return only raw JSON\n'
        '3. Each part must show the actual reading used in the word\n'
        '4. Include all characters (kanji and kana) as separate parts\n\n'
        'Examples of correct format with all of the parts broken up, the word represents all the kanji and kana shown in the word.:\n'
        '{\n'
        '    "kanji": "古い",\n'
        '    "romaji": "furui",\n'
        '    "english": "old",\n'
        '    "parts": [\n'
        '        { "kanji": "古", "romaji": ["fu", "ru"] },\n'
        '        { "kanji": "い", "romaji": ["i"] }\n'
        '     ]\n'
        '}' +
        '{\n'
        '    "kanji": "忙しい",\n'
        '    "romaji": "isogashii",\n'
        '    "english": "busy",\n'
        '    "parts": [\n'
        '        { "kanji": "忙", "romaji": ["i","so","ga"] },\n'
        '        { "kanji": "し", "romaji": ["shi"] },\n'
        '        { "kanji": "い", "romaji": ["i"] }\n'
        '    ]\n'
        '}' +
        '{\n'
        '  "kanji": "新しい",\n'
        '  "romaji": "atarashii",\n'
        '  "english": "new",\n'
        '  "parts": [\n'
        '    { "kanji": "新", "romaji": ["a","ta","ra"] },\n'
        '    { "kanji": "し", "romaji": ["shi"] },\n'
        '    { "kanji": "い", "romaji": ["i"] }\n'
        '  ]\n'
        '}\n\n' +
        'Example of bad format:\n'
        '{\n'
        '  "kanji": "晴れ",\n'
        '  "romaji": "hare",\n'
        '  "english": "sunny",\n'
        '  "parts": [\n'
        '    { "kanji": "晴", "romaji": [\n'
        '       "seki",\n'
        '       "haru"] },\n'
        '  ]\n'
        '}' +
        'Reason for bad example:\n'
        '1. parts of romaji that are shown do not represent the word.\n'
        '2. Instead of listing out seki haru, should just say ha, the kanji representation for hare \n'
        '3. it is missing the other part.\n'
        '4. There should be 2 parts: one for ha and the other for re\n\n'
    )

    try:
        completion = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        
        result = completion.choices[0].message.content
        return json.loads(result)
    except Exception as e:
        print(f"Error generating vocabulary: {str(e)}")
        raise