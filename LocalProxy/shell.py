#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
VERBOSE_LEVEL = 5
verbose = 0


def print_exception(e):
    global verbose
    logging.error(e)
    if verbose > 0:
        import traceback
        traceback.print_exc()