from flask import Flask

def create_app():
   app = Flask(__name__)
   with app.app_context():
      from .routes.home import home
      from .routes.analyze import analyze
      app.register_blueprint(home)
      app.register_blueprint(analyze)
   return app