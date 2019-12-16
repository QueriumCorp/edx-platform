# -*- coding: utf-8 -*-
"""
Exceptions used to implement LTI Willo Labs Grade Sync support in third_party_auth
"""
from __future__ import absolute_import


class LTIBusinessRuleError(Exception):
   """Raised for LTI authentication and data exchange work flows inconsistencies """
   pass
