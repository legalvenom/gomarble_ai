from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import time
import httpx
import json
import logging
from typing import Union, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Review(BaseModel):
    title: str
    body: str
    rating: int
    reviewer: str
    date: Optional[str] = None

class ReviewSelectors(BaseModel):
    container: str
    title: Optional[str]
    rating: Optional[str]
    body: Optional[str]
    reviewer: Optional[str]
    date: Optional[str]
    pagination: Optional[str]

class ScrapingError(Exception):
    pass

async def get_llm_selectors(html_sample: str, url: str) -> ReviewSelectors:
    """Use Ollama's Mistral model to identify CSS selectors for the given page."""
    
    OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
    
    # Define the prompt here
    prompt = f"""Analyze this HTML from {url} and identify the CSS selectors for review elements.
    Return only a JSON object with these keys: container, title, rating, body, reviewer, date, pagination.
    Each value should be a CSS selector string or null if not found.
    Sample HTML:
    {html_sample[:2000]}  # Send first 2000 chars as sample
    """
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("Attempting to connect to Ollama service...")
            
            # Rest of the function remains the same...
            try:
                await client.get("http://localhost:11434/api/version")
                logger.info("Successfully connected to Ollama service")
            except Exception as e:
                logger.error(f"Could not connect to Ollama service: {str(e)}")
                return get_default_selectors()
            
            response = await client.post(
                OLLAMA_ENDPOINT,
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                try:
                    response_text = response.json()["response"]
                    selectors = json.loads(response_text)
                    return ReviewSelectors(**selectors)
                except Exception as e:
                    logger.error(f"Failed to parse LLM response: {str(e)}")
                    return get_default_selectors()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return get_default_selectors()
            
    except Exception as e:
        logger.error(f"Error getting LLM selectors: {str(e)}")
        return get_default_selectors()

def parse_rating(rating_text: str) -> int:
    """Parse rating from text to integer with improved text cleaning.
    
    Args:
        rating_text (str): The rating text to parse
        
    Returns:
        int: Rating value from 1-5
    """
    try:
        # Clean up the input text
        text = rating_text.strip().lower()
        if not text:
            return 5  # Default for empty ratings
            
        # Extract the first number found in the text
        def extract_first_number(text):
            import re
            numbers = re.findall(r'\d+\.?\d*', text)
            return float(numbers[0]) if numbers else None
            
        # Handle "X out of Y" format
        if 'out of' in text:
            parts = text.split('out of')
            if len(parts) >= 2:
                rating_value = extract_first_number(parts[0])
                scale = extract_first_number(parts[1])
                if rating_value is not None and scale is not None:
                    return min(5, max(1, int(round(rating_value * 5 / scale))))
        
        # Handle star ratings (★★★★☆)
        if '★' in text:
            return text.count('★')
            
        # Handle fractional ratings (4/5)
        if '/' in text:
            parts = text.split('/')
            if len(parts) == 2:
                try:
                    num = float(parts[0].strip())
                    denom = float(parts[1].strip())
                    return min(5, max(1, int(round(num * 5 / denom))))
                except ValueError:
                    pass
        
        # Try to extract and parse any number
        rating = extract_first_number(text)
        if rating is not None:
            # If rating is on a 10-point scale, convert to 5-point
            if rating > 5:
                rating = rating / 2
            return min(5, max(1, int(round(rating))))
            
        return 5  # Default if no valid rating found
            
    except Exception as e:
        logger.error(f"Error parsing rating '{rating_text}': {str(e)}")
        return 5  # Default to 5 stars if parsing fails

def setup_driver():
    """Setup Chrome in headless mode with extended capabilities."""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        return webdriver.Chrome(options=options)
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {str(e)}")
        raise ScrapingError(f"Failed to initialize browser: {str(e)}")

def extract_reviews_with_selectors(html_content: str, selectors: ReviewSelectors) -> List[Review]:
    """Extract reviews using provided selectors with improved rating extraction."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        reviews = []
        
        containers = soup.select(selectors.container)
        
        for container in containers:
            try:
                title_elem = container.select_one(selectors.title) if selectors.title else None
                title = title_elem.text.strip() if title_elem else "Review"
                
                # Improved rating extraction
                rating_elem = container.select_one(selectors.rating) if selectors.rating else None
                rating_text = rating_elem.text.strip() if rating_elem else "5"
                
                # For Judge.me specific handling
                if "judge.me" in rating_text.lower():
                    # Try to extract just the numeric rating
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*out of\s*\d+', rating_text)
                    rating_text = match.group(1) if match else "5"
                
                rating = parse_rating(rating_text)
                
                body_elem = container.select_one(selectors.body) if selectors.body else None
                body = body_elem.text.strip() if body_elem else container.text.strip()
                
                reviewer_elem = container.select_one(selectors.reviewer) if selectors.reviewer else None
                reviewer = reviewer_elem.text.strip() if reviewer_elem else "Anonymous"
                
                date_elem = container.select_one(selectors.date) if selectors.date else None
                date = date_elem.text.strip() if date_elem else None
                
                reviews.append(Review(
                    title=title,
                    body=body,
                    rating=rating,
                    reviewer=reviewer,
                    date=date
                ))
                
            except Exception as e:
                logger.error(f"Error extracting review: {str(e)}")
                continue
        
        return reviews
    except Exception as e:
        logger.error(f"Error parsing HTML: {str(e)}")
        return []

@app.get("/api/reviews")
async def get_reviews(url: HttpUrl, max_pages: int = 5):
    driver = None
    try:
        driver = setup_driver()
        all_reviews = []
        current_url = str(url)
        
        # Get initial page
        driver.get(current_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get selectors
        selectors = get_default_selectors()  # Start with default selectors
        
        # Process pages
        page_count = 0
        while current_url and page_count < max_pages:
            logger.info(f"Processing page {page_count + 1}")
            
            # Extract reviews from current page
            reviews = extract_reviews_with_selectors(driver.page_source, selectors)
            all_reviews.extend(reviews)
            
            # Get next page URL
            try:
                next_url = await get_next_page_url(driver, selectors)
                if not next_url or next_url == current_url:
                    break
                    
                current_url = next_url
                driver.get(current_url)
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error navigating to next page: {str(e)}")
                break
                
            page_count += 1
            
        return {
            "reviews_count": len(all_reviews),
            "pages_processed": page_count + 1,
            "reviews": all_reviews
        }
        
    except Exception as e:
        logger.error(f"Error processing reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

def get_default_selectors() -> ReviewSelectors:
    
    return ReviewSelectors(
        container="div[class*='review'], div[class*='comment']",
        title="h3, h4, strong",
        rating="span[class*='rating'], div[class*='stars']",
        body="div[class*='content'], div[class*='text']",
        reviewer="span[class*='author'], span[class*='name']",
        date="span[class*='date']",
        pagination="ul.pagination a, div[class*='pagination'] a"
    )

async def get_next_page_url(driver, selectors: ReviewSelectors) -> Optional[str]:
    """Find next page URL using pagination selectors."""
    try:
        pagination_elements = driver.find_elements(By.CSS_SELECTOR, selectors.pagination)
        for element in pagination_elements:
            if any(next_text in element.text.lower() for next_text in ['next', '›', '»', 'forward']):
                return element.get_attribute('href')
    except Exception as e:
        logger.error(f"Error finding next page: {str(e)}")
    return None
