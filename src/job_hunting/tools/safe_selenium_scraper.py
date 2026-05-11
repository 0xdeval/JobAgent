import time
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class SafeSeleniumScrapingSchema(BaseModel):
    website_url: str = Field(description="Mandatory website url to read. Must start with http:// or https://")
    css_element: Optional[str] = Field(description="Optional css reference for element to scrape from the website", default="")

class SafeSeleniumScrapingTool(BaseTool):
    name: str = "Scrape website with Selenium"
    description: str = "A tool that can be used to read a website content, including dynamically loaded content."
    args_schema: Type[BaseModel] = SafeSeleniumScrapingSchema

    def _run(self, website_url: str, css_element: str = "") -> str:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            driver.get(website_url)
            
            # Wait for initial load
            time.sleep(3)
            
            # Scroll down multiple times to trigger lazy loading
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

            # If a specific CSS element is requested, wait for it
            if css_element:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, css_element))
                    )
                except:
                    pass # Continue anyway if wait fails

            # Specifically for job boards, wait for links to appear
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except:
                pass

            # Extract content
            if css_element:
                elements = driver.find_elements(By.CSS_SELECTOR, css_element)
                content = "\n".join([e.text for e in elements if e.text.strip()])
                # If it's links, also get URLs
                if css_element.startswith("a") or " a" in css_element or css_element.endswith("a"):
                    links = []
                    for e in elements:
                        href = e.get_attribute("href")
                        if href and e.text.strip():
                            links.append(f"[{e.text.strip()}]({href})")
                    if links:
                        content = "\n".join(links)
            else:
                # Default: Get main body text but preserve links in markdown format
                # We'll use a simple heuristic to find job links
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                # Also find all links to provide to the agent
                all_links = driver.find_elements(By.TAG_NAME, "a")
                formatted_links = []
                for link in all_links:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    if href and text and len(text) > 3: # Ignore tiny links
                        # Filter for common job-like links
                        if any(k in href.lower() for k in ["job", "vacancy", "opening", "career", "apply"]):
                             formatted_links.append(f"[{text}]({href})")
                        elif any(k in text.lower() for k in ["engineer", "manager", "lead", "developer", "product", "sales"]):
                             formatted_links.append(f"[{text}]({href})")

                content = page_text
                if formatted_links:
                    content += "\n\n### Potential Job Links Found:\n" + "\n".join(set(formatted_links))

            return content
        except Exception as e:
            return f"Error scraping with Selenium: {str(e)}"
        finally:
            driver.quit()
