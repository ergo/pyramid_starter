# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import logging
import sys

EXCLUDED_LOG_VARS = ['threadName', 'name', 'thread', 'created', 'process',
                     'processName', 'args', 'module', 'filename',
                     'levelno', 'exc_text', 'pathname', 'lineno', 'msg',
                     'exc_info', 'message', 'funcName', 'stack_info',
                     'relativeCreated', 'levelname', 'msecs', 'asctime']


class JSONFormatter(logging.Formatter):
    def format(self, record):
        """
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using LogRecord.getMessage(). If the formatting string uses the
        time (as determined by a call to usesTime(), formatTime() is
        called to format the event time. If there is exception information,
        it is formatted using formatException() and appended to the message.
        """
        record.message = record.getMessage()
        log_dict = vars(record)
        keys = [k for k in log_dict.keys() if k not in EXCLUDED_LOG_VARS]
        _json = {'message': record.message}
        _json.update({k: log_dict[k] for k in keys})
        record.message = json.dumps(_json, default=lambda x: str(x))

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        try:
            s = self._fmt % record.__dict__
        except UnicodeDecodeError as e:
            # Issue 25664. The logger name may be Unicode. Try again ...
            try:
                record.name = record.name.decode('utf-8')
                s = self._fmt % record.__dict__
            except UnicodeDecodeError:
                raise e
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s += "\n"
            try:
                s = s + record.exc_text
            except UnicodeError:
                # Sometimes filenames have non-ASCII chars, which can lead
                # to errors when s is Unicode and record.exc_text is str
                # See issue 8924.
                # We also use replace for when there are multiple
                # encodings, e.g. UTF-8 for the filesystem and latin-1
                # for a script. See issue 13232.
                s = s + record.exc_text.decode(sys.getfilesystemencoding(),
                                               'replace')

        return s
