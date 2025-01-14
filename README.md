# GoMarble Review Extractor

## Project Overview
Review Extractor a web-based application that allows users to scrape reviews from product or service pages, calculate statistics like average ratings, and display results in a user-friendly interface. The application is divided into two parts:

- **Frontend**: Deployed using Render in Static page
- **Backend**: Deployed using Render in Web Service

**URL**: [GoMarble](https://llm-review-scraper-frontend.onrender.com)
**NOTE**: Since im using free deployment instance in Render it may go down when inactive



---

## Directory Structure
```
gomarble/
├── backend/
│   ├── app.py
│   ├── requirements.txt
├── frontend/
│   ├── index.html

```

---

## Features
- Scrapes reviews from specified URLs.
- Displays pages processed and calculates average ratings.
- Allows users to specify the number of pages to scrape.
- Fully responsive frontend with a clean UI.

---

## Frontend

The frontend is built with **HTML**, **CSS**, and **JavaScript**. It communicates with the backend using `fetch` API calls to retrieve review data and display it on the page.

### Deployment
The frontend is deployed using **Render**:

1. Push the `frontend/` folder to a GitHub repository.
2. On Render:
   - Create a new **Static Site**.
   - Link the repository containing the frontend code.
   - Configure the root directory to `frontend/`.
3. Render will automatically deploy the frontend and provide a URL.

**Access the frontend at**: [GoMarble Frontend](https://llm-review-scraper-frontend.onrender.com)

---

## Backend

The backend is built using **FastAPI** and supports the review extraction functionality. It uses libraries such as Selenium and BeautifulSoup for web scraping. Additionally, it leverages **LLMs (Large Language Models)** to dynamically identify CSS selectors for extracting reviews from various websites.

### Key Components:

1. **LLM Integration:**
   - Uses Ollama's Mistral model to identify dynamic CSS selectors for extracting reviews. This helps adapt to different website structures without manual intervention.
   - The function `get_llm_selectors` sends HTML samples to the LLM for analysis and retrieves the appropriate selectors for review containers, titles, ratings, and other elements.

2. **Browser Automation:**
   - Utilizes **Selenium** with Chrome in headless mode for navigating and scraping pages.
   - Supports pagination to extract reviews across multiple pages.

3. **Fallback Selectors:**
   - Provides default CSS selectors to handle scenarios where the LLM fails to generate accurate selectors.

### Deployment
The backend is deployed on Render:

1. Add a `requirements.txt` file for dependencies. Example:
   ```
   fastapi
   uvicorn
   selenium
   beautifulsoup4
   httpx
   ```
2. Push the `backend/` folder to a GitHub repository.
3. On Render:
   - Create a new **Web Service**.
   - Link the repository containing the backend code.
   - Configure the start command to use `uvicorn app:app --host 0.0.0.0 --port $PORT`.

**Access the backend at**: https://llm-review-scraper-backend.onrender.com

---

## How to Run Locally

### Prerequisites
- Python 3.8+
- ChromeDriver (for Selenium)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/legalvenom/gomarble_ai.git
   cd gomarble_ai
   ```

2. **Setup Backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```
   The backend will run at `http://127.0.0.1:8000`.

3. **Setup Frontend**:
   Use a simple HTTP server to serve the frontend locally:
   ```bash
   cd ../frontend
   python -m http.server
   ```
   Access the frontend at `http://127.0.0.1:8000`.

---

## API Documentation

### Endpoint: `/api/reviews`
**Method**: `GET`

**Parameters:**
- `url` (string): The URL of the product or service to scrape reviews from.
**Sample Request:**
```bash
curl -X GET "https://llm-review-scraper-backend.onrender.com/api/reviews?url=${encodeURIComponent(url)}"
```

**Sample Response:**
```json
{
    "pages_processed": 3,
    "reviews": [
        {
            "title": "Great product!",
            "body": "This product exceeded my expectations.",
            "rating": 5,
            "reviewer": "John Doe",
            "date": "2023-12-01"
        },
        {
            "title": "Not bad",
            "body": "Good value for money.",
            "rating": 4,
            "reviewer": "Jane Smith",
            "date": "2023-11-28"
        }
    ]
}
```

---

## System Architecture and Workflow

### Diagram
```plaintext
Frontend (GitHub Pages)
   |
   v
Backend (Render)
   |
   v
Selenium + BeautifulSoup
   |
   v
LLM (Ollama's Mistral Model for Dynamic CSS Identification)
```

### Workflow Explanation
1. **Frontend Interaction:**
   - Users input a URL and the maximum number of pages to scrape.
   - The frontend sends an API request to the backend with these parameters.

2. **Backend Processing:**
   - The backend uses Selenium to navigate the website and extract the HTML content.
   - The extracted HTML is sent to the LLM for dynamic CSS selector identification.
   - If the LLM fails, default selectors are used.
   - Reviews are parsed using the identified selectors, and pagination is handled to scrape multiple pages.

3. **Data Return:**
   - The backend returns the processed reviews, total pages scraped, and average rating to the frontend.
   - The frontend displays the results in a user-friendly format.

---

## Effective Use of LLMs
- The LLM (Ollama's Mistral model) dynamically identifies CSS selectors for:
  - Review containers
  - Titles
  - Ratings
  - Reviewers
  - Dates
- This eliminates the need for hardcoded selectors, making the scraper adaptable to various website structures.

---

## Sample Output Screenshot
**Example Response Display:**
![go1](https://github.com/user-attachments/assets/d2328eb8-72b8-400a-89f6-8c30138a75f2)

![go2](https://github.com/user-attachments/assets/42a0969b-c388-4c00-91b3-ce86ebf4bf8c)



---






