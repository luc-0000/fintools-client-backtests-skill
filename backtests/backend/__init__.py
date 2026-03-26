#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import sys
import os

if not hasattr(sys.modules[__name__], '__file__'):
    __file__ = inspect.getfile(inspect.currentframe())

# APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(os.getcwd())
