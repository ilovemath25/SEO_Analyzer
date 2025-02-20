from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import requests
import json
import re

def analyze_technical(url):
   core_web_vitals = analyze_core_web_vitals(url)
   mobile_friendly = analyze_mobile_friendly(url)
   crawlability = analyze_crawlability(url)
   sitemap = analyze_sitemap(url)
   total_score = round(
      (core_web_vitals["total score"] * 0.25) +
      (mobile_friendly["total score"] * 0.20) +
      (crawlability["total score"] * 0.20) +
      (sitemap["total score"] * 0.15)
   )
   score = [element["total score"] for element in [core_web_vitals, mobile_friendly, crawlability, sitemap]]
   feedback = [element["analysis"] for element in [core_web_vitals, mobile_friendly, crawlability, sitemap]]
   result = {
      "total_score": total_score,
      "detailed_scores": score,
      "feedback": feedback,
   }
   with open("./seo_analyzer_app/utils/technical_seo.json", "w", encoding="utf-8") as f: json.dump(result, f, indent=3, ensure_ascii=False)
   return result
   
def analyze_core_web_vitals(url):
   def get_value(string):
      value = ''
      for s in string: value+=s if s.isdigit() or s == '.' else ''
      return float(value)
   def calculate_score(value, good, poor):
      if value <= good: return round(90 + (1 - (value) / (good)) * 10)
      if value >= poor: return 0
      return round(90 - ((value - good) / (poor - good)) * 90)
   api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=desktop"
   response = requests.get(api_url)
   data = response.json()
   results = data["lighthouseResult"]["audits"]
   lcp = get_value(results["largest-contentful-paint"]["displayValue"])
   fcp = get_value(results["first-contentful-paint"]["displayValue"])
   cls = get_value(results["cumulative-layout-shift"]["displayValue"])
   tbt = get_value(results["total-blocking-time"]["displayValue"])
   tti = get_value(results["interactive"]["displayValue"])
   scores = {
      "LCP": calculate_score(lcp, 2.5, 4.0),
      "FCP": calculate_score(fcp, 1.8, 3.0),
      "CLS": calculate_score(cls, 0.1, 0.25),
      "TBT": calculate_score(tbt, 300, 800),
      "TTI": calculate_score(tti, 3.8, 7.3)
   }
   total_score = round(
      scores["LCP"] * 0.30 +
      scores["CLS"] * 0.25 +
      scores["TBT"] * 0.25 +
      scores["FCP"] * 0.10 +
      scores["TTI"] * 0.10
   )
   return {
      "total score": total_score,
      "analysis": {
         "LCP": scores["LCP"],
         "CLS": scores["CLS"],
         "TBT": scores["TBT"],
         "FCP": scores["FCP"],
         "TTI": scores["TTI"]
      }
   }

def analyze_mobile_friendly(url):
   def analyze_tap_target(url):
      mobile_emulation = {
         "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 },
         "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Mobile Safari/537.36"
      }
      options = webdriver.ChromeOptions()
      options.add_experimental_option("mobileEmulation", mobile_emulation)
      options.add_argument("--headless")
      options.add_argument("--log-level=3")
      options.add_argument("--disable-gpu")
      options.add_argument("--disable-dev-shm-usage")
      driver = webdriver.Chrome(options=options)
      driver.get(url)
      WebDriverWait(driver, 15).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
      driver.execute_script("return document.body.scrollHeight")
      with open("./seo_analyzer_app/utils/tap_target.js", "r") as js_file: tap_target_script = js_file.read()
      tap_targets = driver.execute_script(tap_target_script)
      for t in tap_targets: print(t)
      driver.quit()
      total_elements = len(tap_targets)
      properly_sized = sum(1 for el in tap_targets if el["width"] >= 48 and el["height"] >= 48)
      tap_target_score = (properly_sized / total_elements) * 100 if total_elements > 0 else 100
      return round(tap_target_score)
   api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=desktop"
   response = requests.get(api_url)
   data = response.json()
   results = data["lighthouseResult"]
   lighthouse = results['categories']['performance']['score'] * 100
   viewport = results['audits']['viewport']['score'] * 100
   tap_target = analyze_tap_target(url)
   total_score = (
      (lighthouse * 0.40) +
      (viewport * 0.30) +
      (tap_target * 0.30)
   )
   return {
      "total score": total_score,
      "analysis": {
         "lighthouse": lighthouse,
         "viewport": viewport,
         "tap_targets": tap_target
      }
   }

def analyze_crawlability(url):
   def check_robot_txt(url):
      robots_url = url.rstrip("/") + "/robots.txt"
      response = requests.get(robots_url)
      data = response.text.lower()
      if response.status_code != 200: return {"not_found": True, "score": 0}
      user_agents = re.findall(r"user-agent:\s*([^\n\r]+)", data)
      disallows = re.findall(r"disallow:\s*([^\n\r]*)", data)
      sitemaps = re.findall(r"sitemap:\s*([^\n\r]+)", data)
      googlebot_blocked = "googlebot" in user_agents and "/" in disallows
      return {
         "user_agent": user_agents,
         "disallow": disallows,
         "sitemap": sitemaps,
         "score": 0 if googlebot_blocked else 100
      }
   def check_meta_robots(url):
      response = requests.get(url)
      soup = BeautifulSoup(response.text, "html.parser")
      meta_robots = soup.find("meta", attrs={"name": "robots"})
      if meta_robots:
         content = meta_robots.get("content", "").lower()
         noindex = "noindex" in content
         nofollow = "nofollow" in content
         return {
            "noindex": noindex,
            "nofollow": nofollow,
            "meta_content": content,
            "score": 0 if noindex else 100
         }
      return {"not_found": True, "score": 100}
   def check_canonical(url):
      response = requests.get(url)
      soup = BeautifulSoup(response.text, "html.parser")
      canonical = soup.find("link", attrs={"rel": "canonical"})
      if canonical: return {"href": canonical.get("href", ""), "score": 100}
      return {"not_found": True, "score": 50}
   robots = check_robot_txt(url)
   meta = check_meta_robots(url)
   canonical = check_canonical(url)
   total_score = (
      (robots["score"] * 0.35) +
      (meta["score"] * 0.35) +
      (canonical["score"] * 0.30)
   )
   return {
      "total score": total_score,
      "analysis": {
         "robots": robots,
         "meta": meta,
         "canonical": canonical
      }
   }
   
def analyze_sitemap(url):
   def check_url(link):
      try:
         res = requests.head(link)
         if res.status_code == 200: return "OK"
         elif res.status_code in [301, 302]: return "Redirect"
         elif res.status_code == 404: return "Broken"
      except requests.RequestException: return "Broken"
   sitemap_url = url.rstrip("/") + "/sitemap.xml"
   response = requests.get(sitemap_url)
   if response.status_code != 200: return {"score": 0, "feedback": "No sitemap found"}
   soup = BeautifulSoup(response.content, "xml")
   urls = [loc.text for loc in soup.find_all("loc")]
   status = {url: check_url(url) for url in urls}
   total = len(status)
   broken = sum(status == "Broken" for status in status.values())
   redirects = sum(status == "Redirect" for status in status.values())

   accessible_score = max(0, 100 - (broken / total * 100)) if total else 100
   redirect_score = max(0, 100 - (redirects / total * 100)) if total else 100
   total_score = (accessible_score * 0.7) + (redirect_score * 0.3)
   return {
      "total score": total_score,
      "analysis": status
   }
if __name__=='__main__':
   analyze_technical("https://ilovemath25.github.io")