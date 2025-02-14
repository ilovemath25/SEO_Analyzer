from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from bs4 import BeautifulSoup
from googlesearch import search
import concurrent.futures
import requests
import random
import json
import os
import re

def analyze_rank(url):
   options = webdriver.ChromeOptions()
   options.add_argument("--headless")
   options.add_argument("--log-level=3")
   options.add_argument("--disable-gpu")
   options.add_argument("--disable-dev-shm-usage")
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
   keyword_frequencies = {kw: get_keyword_frequency(kw) for kw, _ in keywords.items()}
   keywords = sorted(keyword_frequencies.items(), key=lambda x: x[1], reverse=True)
   keywords = [kw[0] for kw in keywords]
   positions, notes = check_rank(keywords, url)
   scores = []
   for keyword, rank in positions.items():
      score = 0.4 if rank is None else max(10 - ((rank - 1) * 0.4), 1)
      scores.append([keyword, rank, score])
   total_score = (
      sum(score[2] for score in scores[:3]) * 1.25 +
      sum(score[2] for score in scores[3:6]) * 1.10 +
      sum(score[2] for score in scores[6:]) * 0.90
   )
   result = {
      "total_score": round(total_score, 2),
      "feedback": notes
   }
   with open("./seo_analyzer_app/utils/ranking_seo.json", "w", encoding="utf-8") as f: json.dump(result, f, indent=3, ensure_ascii=False)
   return result

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
   return {kw.replace("_", " "):score for kw, score in keywords}

def get_keyword_frequency(keyword):
   url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
   response = requests.get(url).json()
   suggested_keywords = response[1]
   return suggested_keywords.count(keyword)

def fetch_rank_url(keyword, url):
   url = url.rstrip("/").split("?")[0]
   for i,j in enumerate(search(keyword, tld="com", num=10, stop=10, pause=random.uniform(2, 4))):
      match = re.search(r"https?://[^\s&]+", j)
      result = match.group(0).rstrip("/").split("?")[0] if match else None
      if result and result == url: return keyword, i + 1
   return keyword, None

def check_rank(keywords, url):
   positions = {}
   notes = []
   with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
      futures = {executor.submit(fetch_rank_url, keyword, url): keyword for keyword in keywords}
      for future in concurrent.futures.as_completed(futures):
         keyword, rank = future.result()
         positions[keyword] = rank
         if rank: notes.append(f"Your website ranks #{rank} for keyword '{keyword}'")
         else: notes.append("")
   return positions, notes
