import React, { useState } from "react";
import InputSection from "./InputSection";
import HaikuDisplay from "./HaikuDisplay";
import ImageDisplay from "./ImageDisplay";
import SaveButton from "./SaveButton";
import AnimatedContainer from "./AnimatedContainer";
import { toast } from "@/components/ui/use-toast";
import { useDatabase } from "@/services/DatabaseService";

// Language detection and haiku generation using Mistral-7B-Instruct-v0.2
const detectLanguage = async (word: string): Promise<"en" | "jp"> => {
  try {
    const response = await fetch(
      "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${import.meta.env.VITE_HUGGINGFACEHUB_API_TOKEN}`,
        },
        body: JSON.stringify({
          inputs: `You are a language detection expert. Your task is to identify whether the following word is in English or Japanese.
          Word: ${word}
          Language Reply with just "en" for English or "jp" for Japanese:`,
          parameters: {
            max_new_tokens: 10,
            temperature: 0.1,
          },
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const result = await response.json();
    const output = result[0]?.generated_text || "";

    if (
      output.toLowerCase().includes("jp") ||
      output.toLowerCase().includes("japanese") ||
      output.toLowerCase().includes("日本語")
    ) {
      return "jp";
    } else {
      return "en";
    }
  } catch (error) {
    console.error("Language detection error:", error);
    return "en";
  }
};

const generateHaiku = async (
  word: string,
  language: "en" | "jp"
): Promise<string[]> => {
  try {
    const prompt =
      language === "jp"
        ? `あなたは伝統的な俳句を専門とする創造的なAI詩人です。あなたのタスクは、<<<>>>の後にある単語に基づいて、美しい俳句を次の言語で作成することです：
日本語
その単語が俳句を作成するのに不十分な場合、以下のように分類してください：
insufficient
あなたは、信頼度が最も高い俳句のみを返答します。「俳句」という単語を含めないでください。説明、翻訳、注釈を提供しないでください。
####
以下に例を示します：
単語:夢 
俳句: 夏草や
兵どもが
夢の跡 

単語: 秋  
俳句: 秋深き
隣は何を
する人ぞ  

単語: 釣り 
俳句: 朝顔に
釣瓶取られて
もらい水  

単語: 孤独 
俳句: この道や
住み替はせる
寂しさよ 

###
<<<  
単語: ${word}  
>>>`
        : `You are a creative AI poet specializing in traditional Haiku.. Your task is to Create a beautiful Haiku based on the word after <<<>>> into the following predefined Language:
English
If the word doesn't qualify to be sufficient to create Haiku, classify it as:
insufficient
You will only respond with the generated Haiku that has the maximum confidence score. Do not include the word "Haiku" or "俳句". Do not provide explanations, translations or notes.
####
Here are some examples:
Word: frog
Haiku: An old silent pond...
A frog jumps into the pond,
Splash! Silence again.
Word: light
Haiku: A summer river being crossed
how pleasing
with sandals in my hands.
Word: time
Haiku: Light of the moon
Moves west,
flowers' shadows creep eastward.
Word: dew
Haiku: A world of dew,
And within every dewdrop
A world of struggle.
###
<<<
Word: ${word}
>>>`;

    const response = await fetch(
      "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${import.meta.env.VITE_HUGGINGFACEHUB_API_TOKEN}`,
        },
        body: JSON.stringify({
          inputs: prompt,
          parameters: {
            max_new_tokens: 100,
            temperature: 0.7,
          },
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const result = await response.json();
    const haikuText = result[0]?.generated_text || "";

    const cleanedHaiku = haikuText
      .replace(prompt, "")
      .trim()
      .split("\n")
      .filter((line) => line.trim().length > 0)
      .slice(0, 3);

    console.log("cleanedHaiku:", cleanedHaiku);

    if (cleanedHaiku.length !== 3) {
      if (language === "jp") {
        return ["朝の露", "花びらに映る", "夏の空"];
      } else {
        return ["Morning dewdrops", "Reflecting on petals", "Summer sky above"];
      }
    }

    return cleanedHaiku;
  } catch (error) {
    console.error("Haiku generation error:", error);
    return ["Error generating haiku"];
  }
};

const generateImage = async (haiku: string[]): Promise<string> => {
  try {
    const combinedHaiku = haiku.join(", ");
    const prompt = `A serene artistic interpretation of a haiku: "${combinedHaiku}". Create a traditional Japanese-inspired artwork with subtle colors, minimalist composition, and natural elements.`;

    const response = await fetch(
      "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${import.meta.env.VITE_HUGGINGFACEHUB_API_TOKEN}`,
        },
        body: JSON.stringify({
          inputs: prompt,
          parameters: {
            negative_prompt:
              "text, words, calligraphy, writing, watermarks, signatures",
            guidance_scale: 7,
            num_inference_steps: 30,
          },
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const blob = await response.blob();
    return URL.createObjectURL(blob);
  } catch (error) {
    console.error("Image generation error:", error);
    return "";
  }
};

const saveCreation = async (
  haiku: string[],
  imageUrl: string,
  language: "en" | "jp",
  word: string,
  saveToDatabase: (
    input_word: string,
    language: string,
    haiku_text: string,
    imageUrl: string
  ) => Promise<boolean>
): Promise<void> => {
  try {
    // const fetchImage = async (url: string): Promise<Blob> => {
    //   if (url.startsWith("blob:")) {
    //     const response = await fetch(url);
    //     return await response.blob();
    //   } else if (url.startsWith("data:")) {
    //     const base64Response = await fetch(url);
    //     return await base64Response.blob();
    //   } else {
    //     const imgResponse = await fetch(url);
    //     return await imgResponse.blob();
    //   }
    // };

    // const imageBlob = await fetchImage(imageUrl);

    // const downloadLink = document.createElement("a");
    // downloadLink.href = URL.createObjectURL(imageBlob);
    // downloadLink.download = `haiku-image-${Date.now()}.png`;
    // document.body.appendChild(downloadLink);
    // downloadLink.click();
    // document.body.removeChild(downloadLink);

    const haikuText = haiku.join("\n");
    // const textBlob = new Blob([haikuText], { type: "text/plain" });
    // const textLink = document.createElement("a");
    // textLink.href = URL.createObjectURL(textBlob);
    // textLink.download = `haiku-text-${Date.now()}.txt`;
    // document.body.appendChild(textLink);
    // textLink.click();
    // document.body.removeChild(textLink);

    const dbSuccess = await saveToDatabase(word, language, haikuText, imageUrl);
    if (!dbSuccess) {
      console.warn("Failed to save to database, but files were downloaded");
    }

    console.log("Saving creation:", {
      haiku,
      language,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Save error:", error);
    throw error;
  }
};
interface HaikuGeneratorProps {
  onSave: () => void;
}
const HaikuGenerator: React.FC<HaikuGeneratorProps> = ({onSave}) => {
  const [word, setWord] = useState<string>("");
  const [language, setLanguage] = useState<"en" | "jp">("en");
  const [haiku, setHaiku] = useState<string[]>([]);
  const [imageUrl, setImageUrl] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [hasGenerated, setHasGenerated] = useState<boolean>(false);
  const { saveHaiku } = useDatabase();

  const handleSubmit = async (inputWord: string) => {
    setWord(inputWord);
    setIsGenerating(true);
    setHasGenerated(false);

    try {
      const detectedLanguage = await detectLanguage(inputWord);
      setLanguage(detectedLanguage);

      const generatedHaiku = await generateHaiku(inputWord, detectedLanguage);
      setHaiku(generatedHaiku);

      const generatedImageUrl = await generateImage(generatedHaiku);
      setImageUrl(generatedImageUrl);

      setHasGenerated(true);
      toast({
        title: "Creation complete",
        description: "Your haiku and image are ready to view",
        variant: "default",
      });
    } catch (error) {
      console.error("Generation error:", error);
      toast({
        title: "Generation failed",
        description: "There was a problem creating your haiku and image",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!haiku.length || !imageUrl) return;

    setIsSaving(true);

    try {
      await saveCreation(haiku, imageUrl, language, word, saveHaiku);
      onSave();
    } catch (error) {
      throw error; // SaveButton component will handle this error
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-6xl mx-auto px-4 py-8 space-y-8">
      <InputSection onSubmit={handleSubmit} isLoading={isGenerating} />

      {hasGenerated && (
        <AnimatedContainer animation="fade-in" className="w-full">
          <div className="glass-panel p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
            <HaikuDisplay haiku={haiku} language={language} />

            <div className="flex flex-col space-y-4">
              <ImageDisplay
                imageUrl={imageUrl}
                altText={haiku.join(" ")}
                className="w-full aspect-square md:aspect-auto md:h-80"
              />

              <SaveButton
                onSave={handleSave}
                isSaving={isSaving}
                disabled={!haiku.length || !imageUrl}
                className="w-full mt-4"
              />
            </div>
          </div>
        </AnimatedContainer>
      )}
    </div>
  );
};

export default HaikuGenerator;
