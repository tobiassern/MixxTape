from flask import Flask

# Define app
app = Flask(__name__)

# define runServer that is called in main.py
def runServer():
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5600)

# Import pages.py last as we are calling this file to get the app into pages.py
import pages
