"""WikiArt Base.

License: MIT License (c) 2016

"""
import abc
import json
import os
import time
from typing import Dict, Union
from urllib.parse import unquote

from . import settings


class RequestPadder:
  """Time Lock for requests made to WikiArt server.

    The server supposedly blocks users that make more than 10 requests within
    5 seconds. An active object of this class offers triggers to control the 
    requesting process and pause it for the necessary time.
    """

  def __init__(self):
    self.n_requests_made = 0
    self.time_spent_requesting = 0
    self.local_elapsed = 0

  def request_start(self):
    self.local_elapsed = time.time()

  def request_finished(self):
    self.local_elapsed = time.time() - self.local_elapsed
    self.time_spent_requesting += self.local_elapsed
    self.n_requests_made += 1

    self.pad()

  def pad(self, force=False):
    if self.n_requests_made >= settings.REQUEST_STRIDE:
      # I finished this batch. Let's pad if necessary.
      # It might be the case where my requests took too long and I don't
      # need to pad the next batch.
      if force or self.time_spent_requesting < settings.REQUEST_PADDING_IN_SECS:
        # Wait for the necessary time only.
        time.sleep(settings.REQUEST_PADDING_IN_SECS)

      self.n_requests_made = 0
      self.time_spent_requesting = 0
      self.local_elapsed = 0

  def __enter__(self):
    self.request_start()
    return self

  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.request_finished()


class Paginator:

  def __init__(self, context_file: str = None):
    self.context_file = context_file or os.path.join(
      settings.BASE_FOLDER, 'meta', '_context.json'
    )

    self.request_id = 0
    self.context = None
    self.has_more = True
    self.interrupted = False
    self.params = {}

  def load_context_from_disk(self):
    self.context = (
      load_json(self.context_file) if os.path.exists(self.context_file) else {}
    )

    self.request_id = self.context.get('requestId', 0)
    self.params = {}
    if self.context.get('hasMore'):
      self.params['paginationToken'] = unquote(self.context['paginationToken'])
    if self.context.get('fromDate'):
      self.params['fromDate'] = self.context['fromDate']

    return self

  def save_context_in_disk(self, last_request_at):
    if not self.interrupted:
      self.context['fromDate'] = last_request_at
    save_json(self.context, self.context_file)

  def update(
    self,
    page: Dict[str, Union[bool, str]],
    commit: bool = True,
  ):
    has_more = page.get('hasMore', False)
    pag_token = page.get('paginationToken')

    self.context.update(
      requestId=self.request_id,
      hasMore=has_more,
      paginationToken=pag_token,
    )

    if commit:
      save_json(self.context, self.context_path)

    if has_more:
      self.params['paginationToken'] = unquote(pag_token)

    self.request_id += 1
    self.has_more = has_more

  def interrupt(self):
    self.interrupted = True

  @property
  def running(self):
    return self.has_more and not self.interrupted


class log(metaclass=abc.ABCMeta):
  """Logs Events During Fetching and Conversion."""
  active = False
  keep_messages = False

  messages_ = []

  @classmethod
  def info(cls, message, end='\n', flush=False):
    cls.write(message, 'info', end, flush)

  @classmethod
  def warning(cls, message, end='\n', flush=False):
    cls.write(message, 'warning', end, flush)

  @classmethod
  def error(cls, message, end='\n', flush=False):
    cls.write(message, 'error', end, flush)

  @classmethod
  def write(cls, message, label=None, end='\n', flush=False):
    if cls.keep_messages:
      cls.messages_.append(message)
    if cls.active:
      if label:
        message = label + ': ' + message
      print(message, end=end, flush=flush)


def load_json(file, encoding='utf-8'):
  with open(file, encoding=encoding) as f:
    return json.load(f)


def save_json(data, file, encoding='utf-8'):
  with open(file, 'w', encoding=encoding) as f:
    json.dump(data, f, indent=4, ensure_ascii=False)


## Painters


def get_painters_dir():
  base_dir = settings.BASE_FOLDER
  painters_dir = os.path.join(base_dir, 'meta', 'painters')

  return painters_dir


def load_painters_in_disk(painters_dir):
  return [load_json(os.path.join(painters_dir, p)) for p in os.listdir(painters_dir)]


def save_painters_in_disk(painters, painters_dir):
  for p in painters:
    save_json(p, os.path.join(painters_dir, f'{p["url"]}.json'))
