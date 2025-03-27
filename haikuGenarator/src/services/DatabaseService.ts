import { useState, useEffect } from "react";

export interface StoredHaiku {
  id: number;
  input_word: string;
  language: string;
  haiku_text: string;
  image_data: string;
  created_at: string;
}

export class DatabaseService {
  private apiUrl = "http://localhost:5001/api"; // Update this to match your backend URL

  async saveHaiku(
    input_word: string,
    language: string,
    haiku_text: string,
    imageUrl: string
  ): Promise<boolean> {
    try {
      // Convert blob URL to base64 if needed
      let imageData: string;
      console.log("imageURL:", imageUrl);
      if (imageUrl.startsWith("blob:")) {
        const response = await fetch(imageUrl);
        console.log("response:", response);
        const blob = await response.blob();
        imageData = await this.blobToBase64(blob);
        console.log("imageData:", imageData);
      } else {
        imageData = imageUrl;
      }

      // Send data to backend
      const response = await fetch(`${this.apiUrl}/haikus`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          input_word,
          language,
          haiku_text,
          image_data: imageData,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save haiku");
      }

      return true;
    } catch (error) {
      console.error("Failed to save haiku to database:", error);
      return false;
    }
  }

  async getHaikus(): Promise<StoredHaiku[]> {
    try {
      const response = await fetch(`${this.apiUrl}/haikus`);
      if (!response.ok) {
        throw new Error("Failed to fetch haikus");
      }
      const haikus = await response.json();
      return haikus;
    } catch (error) {
      console.error("Failed to get haikus from database:", error);
      return [];
    }
  }

  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          resolve(reader.result);
        } else {
          reject(new Error("Failed to convert blob to base64"));
        }
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
}

// Singleton instance
export const databaseService = new DatabaseService();

// React hook to interact with the database
export function useDatabase() {
  const [haikus, setHaikus] = useState<StoredHaiku[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHaikus = async () => {
    setLoading(true);
    try {
      const result = await databaseService.getHaikus();
      setHaikus(result);
      setError(null);
    } catch (err) {
      console.error("Error fetching haikus:", err);
      setError("Failed to load haikus from database");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHaikus();
  }, []);

  const saveHaiku = async (
    input_word: string,
    language: string,
    haiku_text: string,
    imageUrl: string
  ) => {
    try {
      const success = await databaseService.saveHaiku(
        input_word,
        language,
        haiku_text,
        imageUrl
      );
      if (success) {
        await fetchHaikus();
        return true;
      }
      return false;
    } catch (err) {
      console.error("Error saving haiku:", err);
      return false;
    }
  };

  return {
    haikus,
    loading,
    error,
    fetchHaikus,
    saveHaiku,
  };
}
