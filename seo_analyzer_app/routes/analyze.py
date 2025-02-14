from flask import Blueprint, request, redirect, url_for, render_template
from seo_analyzer_app.utils.on_page_seo import analyze_elements
from seo_analyzer_app.utils.ranking_seo import analyze_rank
import requests
import threading
import os

analyze = Blueprint('analyze', __name__)

@analyze.route('/analyze', methods=['POST'])
def analyze_url():
   for file in ["on_page_seo", "ranking_seo"]:
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
            analyze1.start()
            analyze2.start()
            return render_template("loading.html", url=url)
         else: return redirect(url_for('home.index', error='URL does not exist.'))
      except: return redirect(url_for('home.index', error='URL does not exist.'))

@analyze.route('/check_status')
def check_status():
   status1 = "pending"
   status2 = "pending"
   if os.path.exists("./seo_analyzer_app/utils/on_page_seo.json"): status1 = "done"
   if os.path.exists("./seo_analyzer_app/utils/ranking_seo.json"): status2 = "done"
   return {
      "task1": status1,
      "task2": status2
   }