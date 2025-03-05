
# Haiku Image Muse - AI-Powered Haiku & Image Generator

Haiku Image Muse is an elegant web application that generates traditional haikus and corresponding artistic images based on a single input word. The application supports both English and Japanese inputs, automatically detecting the language and generating content accordingly.

## Features

- **Language Detection**: Automatically detects whether the input word is in English or Japanese
- **Haiku Generation**: Creates a traditional haiku (5-7-5 syllable pattern) with seasonal references
- **Image Generation**: Produces an artistic image that captures the essence of the haiku
- **Save Functionality**: Downloads both the haiku text and generated image locally
- **Database Storage**: Stores all generated haikus and images in a local SQLite database
- **Haiku Collection**: View your previously generated haikus in a gallery format

## Application Flow

1. **User Input**: User enters a single word (English or Japanese)
2. **Processing**:
   - System detects the language of the input word
   - Generates a haiku in the detected language
   - Creates an image that complements the haiku
3. **Display**: Shows the generated haiku and image side by side
4. **Save Option**: Allows the user to download both the haiku text and image, and stores them in the database
5. **Browse History**: Users can view all their previously generated haikus

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Haiku Image Muse App                        │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────┐     ┌─────────────────────────────┐
│       User Interface      │     │      API Integration         │
├───────────────────────────┤     ├─────────────────────────────┤
│ - Input Component         │     │ - Language Detection (Mistral)│
│ - Haiku Display Component │     │ - Haiku Generation (Mistral) │
│ - Image Display Component │     │ - Image Generation (SD 3.5)  │
│ - Save Button Component   │     │ - Save Functionality         │
│ - History Component       │     │                             │
└───────────────┬───────────┘     └─────────────┬───────────────┘
                │                                │
                ▼                                ▼
┌───────────────────────────┐     ┌─────────────────────────────┐
│   Animation & Styling     │     │     External Services        │
├───────────────────────────┤     ├─────────────────────────────┤
│ - Fade-in animations      │     │ - HuggingFace Inference API │
│ - Glass morphism effects  │     │ - File System (local save)  │
│ - Responsive design       │     │ - SQLite Database           │
└───────────────────────────┘     └─────────────────────────────┘
                                              │
                                              ▼
                                  ┌─────────────────────────────┐
                                  │      Database Layer         │
                                  ├─────────────────────────────┤
                                  │ - SQL.js for local storage  │
                                  │ - Haiku storage & retrieval │
                                  │ - Image storage & display   │
                                  └─────────────────────────────┘
```

## Technical Implementation

- **Frontend**: React, TypeScript, Tailwind CSS
- **UI Components**: shadcn/ui component library
- **API Integration**:
  - Language Detection & Haiku Generation: `mistralai/Mistral-7B-Instruct-v0.2` via Hugging Face Inference API
  - Image Generation: `stabilityai/stable-diffusion-3.5-large` via Hugging Face Inference API
- **Database**: SQLite (implemented with SQL.js for client-side storage)
- **Animation**: Custom animation components with CSS transitions
- **File Operations**: Local file download implementation for haiku text and images

## Environment Setup

1. Clone the repository
2. Install dependencies with `npm install`
3. Create a `.env` file with your Hugging Face API key:
   ```
   HUGGINGFACE_API_KEY=your_api_key_here
   ```
4. Start the development server with `npm run dev`
5. Access the application at `http://localhost:8080`

## Database Schema

The application uses a SQLite database with the following schema:

```sql
CREATE TABLE IF NOT EXISTS haikus (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  input_word TEXT NOT NULL,
  language TEXT NOT NULL,
  haiku_text TEXT NOT NULL,
  image_data BLOB NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## API Keys

This application requires a Hugging Face API key to access the AI models for language detection, haiku generation, and image creation. You can obtain a free API key by:

1. Creating an account at [Hugging Face](https://huggingface.co/)
2. Generating an API key in your account settings
3. Adding the key to your environment variables

## Future Enhancements

- Social sharing capabilities
- Theme customization options
- Advanced settings for image generation parameters
- Export functionality for the entire collection
- Authentication system for multiple users

## What technologies are used for this project?

This project is built with .

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## License

MIT License
