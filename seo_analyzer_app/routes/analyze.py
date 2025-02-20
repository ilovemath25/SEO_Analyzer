from flask import Blueprint, request, redirect, url_for, render_template
from seo_analyzer_app.utils.on_page_seo import analyze_elements
from seo_analyzer_app.utils.ranking_seo import analyze_rank
from seo_analyzer_app.utils.technical_seo import analyze_technical
import requests
import threading
import json
import os

analyze = Blueprint('analyze', __name__)

@analyze.route('/analyze', methods=['POST'])
def analyze_url():
   for file in ["on_page_seo", "ranking_seo", "technical_seo"]:
      if os.path.exists(f"./seo_analyzer_app/utils/{file}.json"): os.remove(f"./seo_analyzer_app/utils/{file}.json")
   if request.method == 'POST':
      url = request.form['url']
      if not url: return redirect(url_for('home.index', error='Please provide the URL.'))
      if not url.startswith('https://') and not url.startswith('http://'): url = f'https://{url}'
      try:
         response = requests.get(url)
         if response.status_code == 200:
            analyze1 = threading.Thread(target=analyze_elements, args=(url,), daemon=True)
            analyze2 = threading.Thread(target=analyze_rank, args=(url,), daemon=True)
            analyze3 = threading.Thread(target=analyze_technical, args=(url,), daemon=True)
            analyze1.start()
            analyze2.start()
            analyze3.start()
            return render_template("loading.html", url=url)
         else: return redirect(url_for('home.index', error='URL does not exist.'))
      except: return redirect(url_for('home.index', error='URL does not exist.'))

@analyze.route('/check_status')
def check_status():
   status1, status2, status3 = "pending", "pending", "pending"
   data1, data2, data3 = {}, {}, {}
   
   if os.path.exists("./seo_analyzer_app/utils/on_page_seo.json"):
      status1 = "done"
      with open("./seo_analyzer_app/utils/on_page_seo.json", "r", encoding="utf-8") as f: data1 = json.load(f)
      os.remove(f"./seo_analyzer_app/utils/on_page_seo.json")
      
   if os.path.exists("./seo_analyzer_app/utils/ranking_seo.json"):
      status2 = "done"
      with open("./seo_analyzer_app/utils/ranking_seo.json", "r", encoding="utf-8") as f: data2 = json.load(f)
      os.remove(f"./seo_analyzer_app/utils/ranking_seo.json")
      
   if os.path.exists("./seo_analyzer_app/utils/technical_seo.json"):
      status3 = "done"
      with open("./seo_analyzer_app/utils/technical_seo.json", "r", encoding="utf-8") as f: data3 = json.load(f)
      os.remove(f"./seo_analyzer_app/utils/technical_seo.json")
      
   if all(status=="done" for status in [status1, status2, status3]):
      with open("./seo_analyzer_app/data/recent_search.json", 'w', encoding="utf-8") as f:
         json.dump({data1, data2, data3}, f, indent=3, ensure_ascii=False)
         
   return {
      "task1": status1,
      "task2": status2,
      "task3": status3,
   }