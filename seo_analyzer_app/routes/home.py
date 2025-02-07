from flask import Blueprint, render_template
import json

home = Blueprint('home', __name__)

@home.route('/')
@home.route('/home')
def index():
   with open('seo_analyzer_app/data/recent_search.json') as f:
      recent_searches = json.load(f)
   return render_template('home.html', recent_searches=recent_searches)