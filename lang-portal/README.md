# Lang-Portal Application

## Overview

The Lang-Portal Application is a comprehensive platform designed to facilitate vocabulary learning through a structured flashcard system, writing Practice and typing tutor as various study activities. It has a dashboard showing Last study sessions, Study progress and Quick Stats. It has a feature of vocabulary word addition.

## Execution Flow

1. **Setup and Installation:**

   - Clone the repository.
   - Navigate to the `lang-portal` directory.
   - Install the dependencies using `npm install` for the frontend and `pip install -r requirements.txt` for the backend.

2. **Frontend Development:**

   - Navigate to the `frontend-react` directory.
   - Start the development server with `npm run dev` to launch the React application using Vite.

3. **Backend Development:**

   - Navigate to the `backend-flask` directory.
   - Run the Flask server using `flask run` to start the backend services.

4. **Build:**

   - For the frontend, run `npm run build` to create a production build.
   - For the backend, ensure all dependencies are correctly set for deployment.

5. **Testing:**
   - Use `npm run lint` for frontend linting.
   - Implement and run tests for both frontend and backend as needed.

## Architecture Overview

### Frontend

- Built with React and TypeScript.
- Uses Vite for development and build processes.
- Tailwind CSS is used for styling.
- Pages include Dashboard, Study Activities, Words, and Groups, each with specific components and API interactions.

### Backend

- Implemented with Flask.
- Provides RESTful API endpoints for frontend interaction.
- Handles data operations and business logic.

### Data Flow

- User interactions on the frontend trigger API requests to the backend.
- Backend processes requests and returns responses to update the frontend UI.
- Data is managed and stored on the backend, with endpoints for various resources like study activities, words, and groups.

## Conclusion

The Lang-Portal Application is designed to provide an engaging and efficient way to learn vocabulary through interactive study sessions and comprehensive data management.
