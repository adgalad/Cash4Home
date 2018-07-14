from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import auth


class AutoLogout(object):
  def __init__(self, get_response):
      self.get_response = get_response

  def __call__(self, request):
      return self.get_response(request)

  def process_request(self, request):
    if not request.user.is_authenticated():
      #Can't log out if not logged in
      return

    try:
      if datetime.now() - request.session['last_touch'] > timedelta( 0, 15, 0):
        auth.logout(request)
        del request.session['last_touch']
        return
    except KeyError:
      pass

    request.session['last_touch'] = datetime.now()