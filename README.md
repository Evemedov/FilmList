# Personal Media Tracker (FilmList)

A highly customizable, microservice-based web application to track your personal media consumption, including Movies, TV Shows, and Anime.

## 📸 Screenshots


## 🌟 Features
- **Comprehensive Media Tracking**: Keep track of your watch status, personal ratings (1-10), and text comments.
- **Automated Metadata**: Integrated with the TMDB API to automatically fetch metadata (genres, global ratings, runtime, release year, screenshots). API responses are cached via Redis.
- **Smart TV Show Tracking**: Cascading episode updates.
- **Advanced Filtering & Search**: Real-time search by title, and advanced filters for genres, watch status, local files, tags, and ratings.
- **Customization**: Support for dark/light themes, and the ability to upload local covers to override API-provided images.

## 🛠 Tech Stack
- **Frontend**: React, Vite, Tailwind CSS, Zustand
- **Backend**: Python 3.13, FastAPI (fully asynchronous)
- **Database**: PostgreSQL (using asyncpg & SQLAlchemy), Alembic (migrations)
- **Caching**: Redis (for external API caching)
- **Deployment**: Docker, Docker Compose, Nginx

## 📋 Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed.
- A TMDB API Key (for movies and tv-shows searching).

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd FilmList
   ```

2. **Set up environment variables (optional):**
   Edit a `.env` file in the root directory to add your TMDB API key (can be added later through the UI):
   ```env
   TMDB_API_KEY=your_tmdb_api_key_here
   ```

3. **Start the application:**
   Run the following command to build and start the containers:
   ```bash
   docker compose up -d --build
   ```
   *Note: Database migrations will run automatically on startup.*

4. **Access the application:**
   - **Frontend UI**: `http://localhost:3001`

## ⚠️ Known Issues
- **Local Covers Persistence**: Custom uploaded cover images are currently stored in the `/tmp` directory of the backend container. This means they will be deleted when the container stops or restarts.
- **Cartoons Category**: "Cartoons" isn't a native distinct media type on TMDB. This category might be removed or merged with TV Shows/Movies in the future.

## 🤖 Acknowledgments
This project was proudly developed with the assistance of **Gemini** and **Claude** AI coding assistants! ✨
