
# Haiku Image Muse - Architecture Documentation

## Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      React Application                           │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Component Layer                           │
├─────────────┬─────────────┬──────────────┬──────────┬───────────┤
│InputSection │HaikuDisplay │ImageDisplay  │SaveButton│HaikuHistory│
└─────────────┴─────────────┴──────────────┴──────────┴───────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Main Component: HaikuGenerator              │
├─────────────────────────────────────────────────────────────────┤
│ - State Management                                               │
│ - API Integration                                                │
│ - Business Logic                                                 │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Integration                           │
├─────────────┬─────────────┬──────────────┬─────────────────────┤
│detectLanguage│generateHaiku│generateImage │DatabaseService      │
└─────────────┴─────────────┴──────────────┴─────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Services & Storage                  │
├─────────────────────┬───────────────────┬─────────────────────┤
│  open AI            │  stabilityai/     │  SQLite Database    │
│  gpt 4omini         │  stable-diffusion │  (SQL.js)           │
└─────────────────────┴───────────────────┴─────────────────────┘
```

## Sequence Diagram

```
┌─────┐       ┌────────────────┐       ┌──────────┐       ┌──────────┐      ┌────────┐
│User │       │HaikuGenerator  │       │gpt  4o AI│       │Stable    │      │Database│
│     │       │                │       │Service   │       │Diffusion │      │Service │
└──┬──┘       └───────┬────────┘       └────┬─────┘       └────┬─────┘      └───┬────┘
   │                  │                     │                  │                │
   │  Enter word      │                     │                  │                │
   │─────────────────►│                     │                  │                │
   │                  │                     │                  │                │
   │                  │  Detect language    │                  │                │
   │                  │────────────────────►│                  │                │
   │                  │                     │                  │                │
   │                  │  Return language    │                  │                │
   │                  │◄────────────────────│                  │                │
   │                  │                     │                  │                │
   │                  │  Generate haiku     │                  │                │
   │                  │────────────────────►│                  │                │
   │                  │                     │                  │                │
   │                  │  Return haiku       │                  │                │
   │                  │◄────────────────────│                  │                │
   │                  │                     │                  │                │
   │                  │                     │  Generate image  │                │
   │                  │─────────────────────────────────────► │                │
   │                  │                     │                  │                │
   │                  │                     │  Return image    │                │
   │                  │◄─────────────────────────────────────-│                │
   │                  │                     │                  │                │
   │  Display results │                     │                  │                │
   │◄─────────────────│                     │                  │                │
   │                  │                     │                  │                │
   │  Click save      │                     │                  │                │
   │─────────────────►│                     │                  │                │
   │                  │                     │                  │                │
   │  Download files  │                     │                  │                │
   │◄─────────────────│                     │                  │                │
   │                  │                     │                  │                │
   │                  │  Save to database   │                  │                │
   │                  │───────────────────────────────────────────────────────►│
   │                  │                     │                  │                │
   │                  │  Confirm save       │                  │                │
   │                  │◄───────────────────────────────────────────────────────│
   │                  │                     │                  │                │
   │  Click history   │                     │                  │                │
   │─────────────────►│                     │                  │                │
   │                  │                     │                  │                │
   │                  │  Fetch haikus       │                  │                │
   │                  │───────────────────────────────────────────────────────►│
   │                  │                     │                  │                │
   │                  │  Return haikus      │                  │                │
   │                  │◄───────────────────────────────────────────────────────│
   │                  │                     │                  │                │
   │  Display history │                     │                  │                │
   │◄─────────────────│                     │                  │                │
   │                  │                     │                  │                │
┌──┴──┐       ┌───────┴────────┐       ┌────┴─────┐       ┌────┴─────┐      ┌───┴────┐
│User │       │HaikuGenerator  │       │gpt 4omini│       │Stable    │      │Database│
│     │       │                │       │Service   │       │Diffusion │      │Service │
└─────┘       └────────────────┘       └──────────┘       └──────────┘      └────────┘
```

## Component Structure

1. **HaikuGenerator** (Main Component)
   - Manages application state
   - Coordinates API calls
   - Handles user interactions

2. **InputSection**
   - Word input field
   - Submit button
   - Loading indicator

3. **HaikuDisplay**
   - Displays generated haiku
   - Handles different languages (English/Japanese)
   - Animation effects

4. **ImageDisplay**
   - Displays generated image
   - Loading states
   - Error handling

5. **SaveButton**
   - Triggers download functionality
   - Saves to database
   - Loading/success states

6. **HaikuHistory**
   - Displays saved haikus from database
   - Grid layout with responsive design
   - Empty state handling

7. **AnimatedContainer**
   - Wrapper component for animations
   - Used throughout the application for consistent animation effects

## Data Flow

1. User enters a word in the InputSection
2. HaikuGenerator processes the input:
   - Calls detectLanguage API to determine if English or Japanese
   - Calls generateHaiku API to create a haiku in the appropriate language
   - Calls generateImage API to create an image based on the haiku
3. Results are displayed in the HaikuDisplay and ImageDisplay components
4. User can save the results using the SaveButton, which:
   - Triggers local downloads of the haiku text and image
   - Saves the haiku and image to the SQLite database
5. User can switch to the History view to see all saved haikus
6. HaikuHistory component fetches and displays all saved haikus from the database

## API Integration

The application uses the Hugging Face Inference API to access two key models:

1. **gpt 4o mini**:
   - Used for language detection
   - Used for haiku generation with appropriate prompts

2. **stabilityai/stable-diffusion-3.5-large**:
   - Used for image generation based on the haiku content

## Database Integration

The application uses SQL.js to provide a client-side SQLite database:

1. **Database Schema**:
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

2. **Operations**:
   - Initialize database and create table if it doesn't exist
   - Save generated haikus and images to the database
   - Retrieve and display saved haikus
   - Database persistence using localStorage

## State Management

State is managed locally within the HaikuGenerator component using React's useState hooks:

- `word`: Stores the user input
- `language`: Tracks detected language ('en' or 'jp')
- `haiku`: Stores the generated haiku lines
- `imageUrl`: Stores the URL for the generated image
- `isGenerating`: Loading state for generation process
- `isSaving`: Loading state for save process
- `hasGenerated`: Tracks if content has been generated
- `activeTab`: Controls which tab is currently displayed (create or history)

## Error Handling

- API errors are caught and logged
- Fallback content is provided in case of generation failures
- Database errors are handled gracefully with informative messages
- Empty state handling for database with no saved haikus

## Styling and UX

- Responsive design using Tailwind CSS
- Glass morphism effects for containers
- Animated transitions for UI elements
- Japanese vertical writing mode for Japanese haikus
- Tab-based navigation between creation and history views
