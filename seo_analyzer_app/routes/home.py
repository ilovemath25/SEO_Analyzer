from flask import Blueprint, render_template, request
import json

home = Blueprint('home', __name__)

@home.route('/', methods=['GET', 'POST'])
@home.route('/home', methods=['GET', 'POST'])
def index():
   error = request.args.get('error')
   with open('seo_analyzer_app/data/recent_search.json') as f: recent_searches = json.load(f)
   if len(recent_searches) > 3: recent_searches = recent_searches[:3]
   return render_template('home.html', recent_searches=recent_searches, error=error)