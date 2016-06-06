#!/usr/bin/python3.4
#
#     util.py
#
# Utility functions
#
#############################################################

import sys
import re
import itertools as it
import operator as op

def striplines(lines):
    """ Removes empty strings only at the beginning and the end of a list of strings.
        Empty strings in the middle are kept without change.

        All strings are stripped.

    Args:
        lines (list): Lines of text.

    yields:
        str: Line of modified list.

    Examples:
        >>> list(striplines(['','', 'a','b','', 'c', '', '', 'd', '']))
        ['a', 'b', '', 'c', '', 'd']

    """
    lines = [list(g) for k,g in it.groupby(l.strip() for l in lines)]
    
    if not any(l.strip() for l in lines[0]): lines.pop(0)
    if not any(l.strip() for l in lines[-1]): lines.pop(-1)

    for line in lines:
        yield line[0]

def subsequences(seq):
    """ Arrange list of numbers in ordered subsequnces.

    Args:
        seq (iterable): List of numbers containing subsequences.

    Returns:
        list: Sublists of numbers groupped in sequences.

    Examples:
        >>> subsequences([1,2, 1,2,3, 1, 1, 3,4, 4,5,6, 1])
        [[1, 2], [1, 2, 3], [1], [1], [3, 4], [4, 5, 6], [1]]

    """
    groupped = it.groupby(enumerate(seq), lambda x: x[0]-x[1])
    return [list(map(op.itemgetter(1), g)) for k,g in groupped]


def tochar(*args):
    """ Convert each hex str given in args to corresponding char.

    Args:
        args: Variable number of strings.

    Returns:
        tuple: Chars corresponding to input hex strings.
        
    """
    return tuple(chr(int(s, 16)) for s in args)

def isArabicalpha(c):
    """ Tells if a character is inside the Arabic alphabetic range.

    Arabic range is considered from U+0621 (hamza) until U+0652 (sukun).

    Args:
        c (str): Character to check.

    Returns:
        bool: True if the character is inside the Arabic alphabetic tange,
            False otherwise.

    """
    return ord(c)>=ord('ء') and ord(c)<=ord('ْ')