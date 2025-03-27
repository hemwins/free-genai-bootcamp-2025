"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { generateVocabulary } from "../services/generateVocabulary"
import { postVocabulary, VocabularyItem } from "@/services/api"
import { JsonView, allExpanded, defaultStyles } from 'react-json-view-lite';
import 'react-json-view-lite/dist/index.css';

export default function VocabularyImporter() {
  const [category, setCategory] = useState("")
  const [savedCount, setSavedCount] = useState<number | null>(null)

  const [result, setResult] = useState<[VocabularyItem] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      const data = await generateVocabulary(category)
      setResult(data)
    } catch (error) {
      console.error("Error generating vocabulary:", error)
      setError("Error generating vocabulary:" + error)
    } finally {
      setIsLoading(false)
    }
  }
  useEffect(() => {
    if (result) {
      const saveVocabulary = async () => {
        try {
          const count = await postVocabulary(result, category);
          setSavedCount(count);
        } catch (error) {
          console.error("Error saving vocabulary:", error);
          setError("Error saving vocabulary: " + error);
          setSavedCount(null);
        }
      };
      saveVocabulary();
    }
  }, [result, category])

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold mb-4">Vocabulary Generator</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">Category</label>
        <Input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Enter thematic category (e.g., weather, food, emotions)"
          className="w-full"
          />
      </div>      
        <Button type="submit" disabled={isLoading} className="w-full">
          {isLoading ? "Generating..." : "Generate Vocabulary"}
        </Button>
      </form>
      {result && ( <>
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <pre className="whitespace-pre-wrap overflow-x-auto">
              {error || `${savedCount} words saved`}
            </pre>
          </div>
        </div>
      <JsonView data={result} shouldExpandNode={allExpanded} style={defaultStyles} /></>
      )
      }
    </div>
  )
}

