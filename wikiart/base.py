"""WikiArt Base.

Author: Lucas David -- <ld492@drexel.edu>
License: MIT License (c) 2016

"""
import abc
import time

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


class Logger(metaclass=abc.ABCMeta):
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
        if cls.keep_messages: cls.messages_.append(message)
        if cls.active:
            if label: message = label + ': ' + message
            print(message, end=end, flush=flush)
