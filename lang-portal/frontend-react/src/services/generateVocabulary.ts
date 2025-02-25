import { generateVocabularyFromLLM } from "../lib/llm"

export async function generateVocabulary(category: string) {
  try {
    const result = await generateVocabularyFromLLM(category)
    return result
  } catch (error) {
    console.error("Error in generateVocabulary:", error)
    throw new Error("Failed to generate vocabulary")
  }
}

