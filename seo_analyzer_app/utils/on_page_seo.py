from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import re
import json

def analyze_elements(url):
   try:
      options = webdriver.ChromeOptions()
      options.add_argument("--headless")
      options.add_argument("--log-level=3")
      options.add_argument("--disable-gpu")
      options.add_argument("--disable-dev-shm-usage")
      driver = webdriver.Chrome(options=options)
      driver.get(url)
      WebDriverWait(driver, 15).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
      html_content = driver.page_source
      soup = BeautifulSoup(html_content, "html.parser")
      title = analyze_title(soup)                        # Score = 10
      meta_description = analyze_meta_description(soup)  # Score = 10
      headers = analyze_headers(soup)                    # Score = 10
      images = analyze_images(soup)                      # Score = 10
      anchors = analyze_anchors(soup, url)               # Score = 10
      feedback = [
         element.get("type", element.get("analysis", "No feedback available")) 
         for element in [title, meta_description, headers, images, anchors]
      ]
      score = [element["score"] for element in [title, meta_description, headers, images, anchors]]
      total_score = (sum(score) / 50) * 100
      result = {
         "total_score": round(total_score, 2),
         "detailed_scores": score,
         "feedback": feedback
      }
      with open("./seo_analyzer_app/utils/on_page_seo.json", "w", encoding="utf-8") as f: json.dump(result, f, indent=3, ensure_ascii=False)
      return result
   except Exception as e: return {"error": f"Failed to fetch the webpage: {str(e)}"}
   finally:
      if driver: driver.quit()
def analyze_title(soup):
   title = soup.find("title")
   title_text = title.text if title else ""
   length = len(title_text)
   if length == 0: return {"score": 0, "type": "No title provided"}
   elif 50 <= length <= 60: return {"score": 10, "type": "Perfect"}
   elif 40 <= length < 50: return {"score": 7, "type": "Good, but could be more descriptive"}
   elif 61 <= length <= 70: return {"score": 5, "type": "Good, but might be too long"}
   elif 30 <= length < 40: return {"score": 3, "type": "Too short, consider adding more detail"}
   elif 71 <= length <= 80: return {"score": 3, "type": "Too long, consider shortening"}
   elif length < 30: return {"score": 0, "type": "Title too short"}
   else: return {"score": 0, "type": "Title too long"}

def analyze_meta_description(soup):
   meta_desc =  soup.find("meta", attrs={"name": "description"})
   description = meta_desc.get("content", "") if meta_desc else ""
   length = len(description)
   if length == 0: return {"score": 0, "type": "No meta description provided"}
   elif 120 <= length <= 160: return {"score": 10, "type": "Perfect"}
   elif 80 <= length <119: return {"score": 5, "type": "Good, but could be more descriptive"}
   elif 161 <= length <= 180: return {"score": 5, "type": "Good, but might be too long"}
   elif length < 80: return {"score": 0, "type": "Meta description too short"}
   else: return {"score": 0, "type": "Meta description too long"}

def analyze_headers(soup):
   headers = {
      "h1": [h.text.strip() for h in soup.find_all("h1")],
      "h2": [h.text.strip() for h in soup.find_all("h2")],
      "h3": [h.text.strip() for h in soup.find_all("h3")]
   }
   analysis = {}
   h1_count = len(headers["h1"])
   if h1_count == 0: analysis["h1"] = {"score": 0, "type": "No h1 tag found"}
   elif h1_count == 1: analysis["h1"] = {"score": 10, "type": "Perfect"}
   elif h1_count == 2: analysis["h1"] = {"score": 5, "type": f"Multiple h1 tags found ({h1_count})"}
   else: analysis["h1"] = {"score": 3, "type": f"Too many h1 tags ({h1_count})"}
   h2_count = len(headers["h2"])
   if h2_count == 0: analysis["h2"] = {"score": 3, "type": "No h2 tags found"}
   else: analysis["h2"] = {"score": 10, "type": "Perfect"}
   h3_count = len(headers["h3"])
   if h3_count == 0: analysis["h3"] = {"score": 3, "type": "No h3 tags found"}
   else: analysis["h3"] = {"score": 10, "type": "Perfect"}
   score = (analysis["h1"]["score"] * 0.5) + (analysis["h2"]["score"] * 0.3) + (analysis["h3"]["score"] * 0.2)
   return {"score": score, "analysis": analysis}

def analyze_images(soup):
   images = soup.find_all("img")
   length = len(images)
   if length == 0: return {"score": 5, "analysis": "No image provided"}
   analysis = {}
   for img in images:
      alt = img.get("alt", "").strip()
      if not alt: analysis[str(img)] = {"score": 0, "type": "No alt in image"}
      else: analysis[str(img)] = {"score": 10, "type": "Perfect"}
   score = sum(item["score"] for item in analysis.values()) / length
   return {"score": score, "analysis": analysis}

def analyze_anchors(soup, url):
   GENERIC_ANCHORS = {
      "click here", "read more", "more", "learn more", "this link", "go here", "visit this",
      "find out more", "continue", "next", "previous", "back", "start", "details", "info",
      "explore", "watch here", "see more", "view", "open", "submit"
   }
   anchors = soup.find_all("a")
   analysis = {}
   domain = urlparse(url).netloc
   for a in anchors:
      anchor_str = re.match(r"<a [^>]+>", str(a))
      anchor_str = anchor_str.group(0) if anchor_str else str(a)
      href = a.get("href")
      anchor_text = a.get_text(" ", strip=True).lower()
      aria_label = a.get("aria-label", "").strip()
      title = a.get("title", "").strip()
      contains_element = bool(a.find())
      best_text = anchor_text or aria_label or title
      if not href:
         analysis[anchor_str] = {"score": 0, "type": "No href in anchor"}
         continue
      href = href.strip()
      url_href = urljoin(url, href)
      if urlparse(url_href).netloc == domain:
         try:
            response = requests.head(url_href, allow_redirects=True, timeout=3)
            if response.status_code >= 400: analysis[anchor_str] = {"score": 0, "type": "Broken internal link"}
            else: analysis[anchor_str] = {"score": 10, "type": "Perfect internal link"}
         except requests.exceptions.RequestException: analysis[anchor_str] = {"score": 0, "type": "Broken internal link"}
      else: analysis[anchor_str] = {"score": 10, "type": "External link (not affecting internal SEO)"}
      if not best_text:
         if contains_element:
            analysis[anchor_str]["score"] -= 3
            analysis[anchor_str]["type"] = "Anchor contains element but no text"
         else:
            analysis[anchor_str]["score"] -= 5
            analysis[anchor_str]["type"] = "Empty anchor text"
      if best_text in GENERIC_ANCHORS:
         analysis[anchor_str]["score"] -= 3
         analysis[anchor_str]["type"] = "Generic anchor text (bad for SEO)"
   length = len(anchors)
   if length == 0: return {"score": 0, "analysis": "No internal links found"}
   score = sum(item["score"] for item in analysis.values()) / max(3,length)
   return {"score": score, "analysis": analysis}