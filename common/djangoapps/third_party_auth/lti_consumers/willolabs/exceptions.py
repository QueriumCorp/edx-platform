# -*- coding: utf-8 -*-
"""
  Exceptions used to implement LTI Willo Labs Grade Sync support in third_party_auth

  Written by:   mcdaniel
                lpm0073@gmail.com
                https://lawrencemcdaniel.com

  Date:         Jan-2020

"""
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
