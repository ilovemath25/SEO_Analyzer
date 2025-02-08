from flask import Blueprint, request, redirect, url_for
from seo_analyzer_app.utils.on_page_seo import analyze_elements
import requests
analyze = Blueprint('analyze', __name__)

@analyze.route('/analyze', methods=['POST'])
def analyze_url():
   if request.method == 'POST':
      url = request.form['url']
      if not url: return redirect(url_for('home.index', error='Please provide the URL.'))
      if not url.startswith('https://') and not url.startswith('http://'): url = f'https://{url}'
      try:
         response = requests.get(url)
         if response.status_code == 200:
            return f"{analyze_elements(url)}"
         else: return redirect(url_for('home.index', error='URL does not exist.'))
      except: return redirect(url_for('home.index', error='URL does not exist.'))
