# 🎵 YouTube Custom Player & Queue

A sleek, modern, and lightweight YouTube Music Player web application built with a Python backend and a responsive HTML5/CSS3/JS frontend. This player allows you to search for songs, manage a playback queue, and enjoy a custom-themed interface without the clutter of the standard YouTube site.

## ✨ Features

-   **Modern UI/UX:** A dark-themed, responsive interface designed for a premium music listening experience.
-   **YouTube Search:** Integrated search functionality to find any song or video directly from YouTube.
-   **Smart Queue Management:** Add songs to your queue, reorder them, and enjoy continuous playback.
-   **Related Recommendations:** Automatically fetches related songs based on what you're currently listening to.
-   **Custom Player Controls:** Full control over playback with play/pause, skip, previous, volume, and seek functionality.
-   **Quick Search Chips:** One-tap search for popular genres and moods (e.g., Lofi, Bollywood, Gaming, Chill).
-   **Mobile Friendly:** Responsive design that works great on both desktop and mobile devices.
-   **No API Key Required:** Uses `yt-dlp` on the backend to fetch search results without needing a Google Cloud API key.

## 🚀 Getting Started

### Prerequisites

-   **Python 3.x** installed on your machine.
-   **pip** (Python package installer).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/YouTube_Custom_Player.git
    cd YouTube_Custom_Player
    ```

2.  **Install dependencies:**
    This project uses `yt-dlp` to interact with YouTube.
    ```bash
    pip install yt-dlp
    ```

### Running the Application

1.  **Start the backend server:**
    ```bash
    python server.py
    ```
2.  **Access the player:**
    Open your web browser and navigate to `http://localhost:8000`.

## 🛠️ Technologies Used

-   **Frontend:**
    -   HTML5 & CSS3 (Custom properties, Grid, Flexbox)
    -   Vanilla JavaScript (ES6+)
    -   [YouTube IFrame Player API](https://developers.google.com/youtube/iframe_api_reference)
    -   [FontAwesome](https://fontawesome.com/) for icons
-   **Backend:**
    -   Python `http.server` for serving static files and API requests.
    -   [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube search and metadata extraction.

## 📂 Project Structure

```text
YouTube_Custom_Player/
├── index.html      # The main frontend application
├── server.py       # Python backend & API handler
└── README.md       # Project documentation
```

## 📝 API Endpoints

The backend provides the following internal API endpoints:

-   `GET /api/search?q=<query>`: Returns a list of search results from YouTube.
-   `GET /api/related?title=<song_title>&id=<video_id>`: Returns related song recommendations.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you have any improvements or new features in mind.

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).

---

*Note: This project is for educational purposes. Please respect YouTube's Terms of Service.*
