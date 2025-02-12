from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from bs4 import BeautifulSoup
import asyncio
import os
import re

def load_model(path):
   model_path = path
   if os.path.exists(model_path): return SentenceTransformer(model_path)
   raise FileNotFoundError("No models found")

def get_keyword(text, model, top_n):
   fixed_text = text.strip().replace('-','_')
   keywords = model.extract_keywords(
      fixed_text, 
      keyphrase_ngram_range = (1, 3),
      stop_words = 'english',
      use_maxsum = True,
      use_mmr = True,
      diversity = 0.3,
      top_n = top_n
   )
   # return {kw.replace("_", " "):score for kw, score in keywords}
   return [kw.replace("_", " ") for kw, _ in keywords]

def extract_url(google_url):
   match = re.search(r"/url\?q=(https?://[^&]+)", google_url)
   return match.group(1) if match else None

def get_chrome_options():
   options = Options()
   options.add_argument("--headless")
   options.add_argument("--no-sandbox")
   options.add_argument("--disable-dev-shm-usage")
   options.add_argument("start-maximized")
   options.add_argument("disable-infobars")
   options.add_argument("--disable-blink-features=AutomationControlled")
   options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
   return options
   
def fetch_page(url):
   options = get_chrome_options()
   driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
   driver.get(url)
   WebDriverWait(driver, 15).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
   soup = BeautifulSoup(driver.page_source, "html.parser")
   search_results = []
   for link in soup.find_all("a"):
      title = link.find("h3")
      url = extract_url(link.get("href"))
      if title and url: search_results.append(url)
   driver.quit()
   return search_results

async def fetch_google_result(keyword):
   loop = asyncio.get_running_loop()
   task1 = loop.run_in_executor(None, fetch_page, f"https://www.google.com/search?q={keyword}")
   task2 = loop.run_in_executor(None, fetch_page, f"https://www.google.com/search?q={keyword}&start=20")
   results = await asyncio.gather(task1, task2)
   return [result for page_results in results for result in page_results]

async def check_rank(keywords, url):
   tasks = [fetch_google_result(keyword) for keyword in keywords]
   results = await asyncio.gather(*tasks)
   positions = {}
   for i, keyword in enumerate(keywords):
      page_results = results[i]
      if any(url in result for result in page_results): position = next((i + 1 for i, result in enumerate(page_results) if url in result), None)
      else: position = None
      positions[keyword] = position
   return position

def analyze_rank(url):
   options = get_chrome_options()
   driver = webdriver.Chrome(options=options)
   driver.get(url)
   WebDriverWait(driver, 15).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
   soup = BeautifulSoup(driver.page_source, "html.parser")
   title = soup.find("title")
   meta_desc =  soup.find("meta", attrs={"name": "description"})
   text = title.text if title else ""
   text += " " + meta_desc.get("content", "") if meta_desc else ""
   text += " " + soup.get_text(separator=" ", strip=True)
   model = load_model("./seo_analyzer_app/models/fine_tuned_seo_model")
   kw_model = KeyBERT(model)
   keywords = get_keyword(text, kw_model, 10)
   print(keywords)
   # asyncio.run(check_rank(keywords, url))

if __name__=='__main__':
   analyze_rank("https://ilovemath25.github.io")