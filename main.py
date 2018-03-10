from flask import Flask

import logging
import sidebarbot

app = Flask(__name__)

@app.route('/healthz')
def healthz():
  """Return a friendly HTTP greeting."""
  return 'ok'

@app.route('/update-knicks-sidebar')
def update_knicks_sidebar():
  """Updates the /r/nyknicks sidebar."""
  sidebarbot.execute()
  return 'Done.'

@app.errorhandler(500)
def server_error(e):
  logging.exception('An error occurred during a request.')
  return """
  An internal error occurred: <pre>{}</pre>
  See logs for full stacktrace.
  """.format(e), 500

if __name__ == '__main__':
  # This is used when running locally. Gunicorn is used to run the
  # application on Google App Engine. See entrypoint in app.yaml.
  # app.run(host='127.0.0.1', port=8080, debug=True)
  app.run(host='0.0.0.0', port=8080, debug=True)
