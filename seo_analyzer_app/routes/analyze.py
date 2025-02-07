from flask import Blueprint, request, redirect, url_for
import requests

analyze = Blueprint('analyze', __name__)

@analyze.route('/analyze', methods=['GET', 'POST'])
def analyze_url():
   if request.method == 'POST':
      url = request.form['url']
      if not url.startswith('https://') and not url.startswith('http://'):
         url = f'https://{url}'
      try:
         response = requests.get(url)
         if response.status_code == 200:
            return f"<p>{url} exists on the internet.</p>"
         else: return redirect(url_for('home.index', error='URL does not exist.'))
      except: return redirect(url_for('home.index', error='URL does not exist.'))