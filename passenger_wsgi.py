import imp
import os
import sys

os.environ['TZ'] = 'America/New_York'
sys.path.insert(0, os.path.dirname(__file__))

wsgi = imp.load_source('wsgi', 'app.py')
application = wsgi.app
