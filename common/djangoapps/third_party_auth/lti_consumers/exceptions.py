# -*- coding: utf-8 -*-
"""Exceptions used to implement LTI Grade Sync support in third_party_auth"""
from __future__ import absolute_import

class LTIBusinessRuleError(Exception):
   """Raised for LTI authentication and data exchange work flows inconsistencies """
   pass

class DatabaseNotReadyError(IOError):
    """
    Subclass of IOError to indicate the database has not yet committed
    the data we're trying to find.
    """
    pass
