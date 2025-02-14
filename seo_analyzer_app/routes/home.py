from flask import Blueprint, render_template, request
import json
import os

home = Blueprint('home', __name__)

@home.route('/', methods=['GET', 'POST'])
@home.route('/home', methods=['GET', 'POST'])
def index():
   for file in ["on_page_seo", "ranking_seo"]:
      if os.path.exists(f"./seo_analyzer_app/utils/{file}.json"): os.remove(f"./seo_analyzer_app/utils/{file}.json")
   error = request.args.get('error')
   with open('seo_analyzer_app/data/recent_search.json') as f: recent_searches = json.load(f)
   if len(recent_searches) > 3: recent_searches = recent_searches[:3]
   return render_template('home.html', recent_searches=recent_searches, error=error)