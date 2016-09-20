#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAvOC - Jinja2 filters
"""

import re

def filter_match_dict(value, pattern, key, ignorecase=False):
    """
    Return first pattern match of value
    """
    matches = []

    if key is None or pattern is None:
        return value

    if ignorecase:
        flags = re.I
    else:
        flags = 0

    _re = re.compile(pattern)
    for v in value:
        if _re.match(v.__getattribute__(key)):
            matches.append(v)

    return matches
