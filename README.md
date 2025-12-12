# News Dashboard

News Dashboard is a simple web application that uses Google Gemini to generate summaries of news articles from RSS feeds.

It is designed to be run on a Raspberry Pi and can be accessed via a web browser.

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/news-dashboard.git
cd news-dashboard
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export GEMINI_API_KEY=your_gemini_api_key
```

4. Run the application:

```bash
python app.py
```

The application will start on `http://localhost:5000`.
