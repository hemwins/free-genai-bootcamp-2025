import initSqlJs from 'sql.js';
import { useState, useEffect } from 'react';

export interface StoredHaiku {
  id: number;
  input_word: string;
  language: string;
  haiku_text: string;
  image_data: string; // Base64 encoded image data
  created_at: string;
}

export class DatabaseService {
  private dbName = 'haiku_generator.db';
  
  constructor() {
    this.initializeDatabase();
  }

  private async initializeDatabase(): Promise<void> {
    try {
      // Open a connection to the database
      const SQL = await initSqlJs({
        locateFile: (file) => `../../sql-wasm/sql-wasm.wasm`
      });
      const db = new SQL.Database();
      
      // Create the haikus table if it doesn't exist
      db.run(`
        CREATE TABLE IF NOT EXISTS haikus (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          input_word TEXT NOT NULL,
          language TEXT NOT NULL,
          haiku_text TEXT NOT NULL,
          image_data BLOB NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      // Save the database to localStorage
      const data = db.export();
      const buffer = new Uint8Array(data);
      const blob = new Blob([buffer]);
      
      // Convert to base64 and save
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          localStorage.setItem(this.dbName, reader.result);
        }
      };
      
      db.close();
    } catch (error) {
      console.error('Failed to initialize database:', error);
    }
  }

  async saveHaiku(input_word: string, language: string, haiku_text: string, imageUrl: string): Promise<boolean> {
    try {
      // First, convert imageUrl to base64 if it's a blob URL
      let imageData: string;
      if (imageUrl.startsWith('blob:')) {
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        imageData = await this.blobToBase64(blob);
      } else {
        imageData = imageUrl;
      }
      
      // Open a connection to the database
      const sql = await import('sql.js').then(SQL => SQL.default);
      const dbData = localStorage.getItem(this.dbName);
      
      if (!dbData) {
        await this.initializeDatabase();
        return this.saveHaiku(input_word, language, haiku_text, imageUrl);
      }
      
      // Convert base64 string back to Uint8Array
      const binaryString = atob(dbData.split(',')[1]);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const db = new sql.Database(bytes);
      
      // Insert the new haiku
      db.run(`
        INSERT INTO haikus (input_word, language, haiku_text, image_data)
        VALUES (?, ?, ?, ?)
      `, [input_word, language, haiku_text, imageData]);
      
      // Save the updated database
      const data = db.export();
      const buffer = new Uint8Array(data);
      const blob = new Blob([buffer]);
      
      // Convert to base64 and save
      const base64data = await this.blobToBase64(blob);
      localStorage.setItem(this.dbName, base64data);
      
      db.close();
      return true;
    } catch (error) {
      console.error('Failed to save haiku to database:', error);
      return false;
    }
  }

  async getHaikus(): Promise<StoredHaiku[]> {
    try {
      const sql = await import('sql.js').then(SQL => SQL.default);
      const dbData = localStorage.getItem(this.dbName);
      
      if (!dbData) {
        await this.initializeDatabase();
        return [];
      }
      
      // Convert base64 string back to Uint8Array
      const binaryString = atob(dbData.split(',')[1]);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const SQL = await initSqlJs({
        locateFile: (file) => `../../sql-wasm/sql-wasm.wasm`
      });
      const db = new SQL.Database();
      
      // Get all haikus
      const results = db.exec('SELECT * FROM haikus ORDER BY created_at DESC');
      db.close();
      
      if (results.length === 0 || !results[0].values) {
        return [];
      }
      
      // Convert results to StoredHaiku array
      return results[0].values.map((row) => {
        return {
          id: row[0] as number,
          input_word: row[1] as string,
          language: row[2] as string,
          haiku_text: row[3] as string,
          image_data: row[4] as string,
          created_at: row[5] as string
        };
      });
    } catch (error) {
      console.error('Failed to get haikus from database:', error);
      return [];
    }
  }

  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to convert blob to base64'));
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
      console.error('Error fetching haikus:', err);
      setError('Failed to load haikus from database');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHaikus();
  }, []);

  const saveHaiku = async (input_word: string, language: string, haiku_text: string, imageUrl: string) => {
    try {
      const success = await databaseService.saveHaiku(input_word, language, haiku_text, imageUrl);
      if (success) {
        await fetchHaikus();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Error saving haiku:', err);
      return false;
    }
  };

  return {
    haikus,
    loading,
    error,
    fetchHaikus,
    saveHaiku
  };
}
