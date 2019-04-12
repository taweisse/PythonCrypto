"""Helper methods to solve common problems.
"""
import os
import re

def readLastLine(f):
    """Reads the last line from an open file object.
    
    Arguments:
        f {file} -- The file object to read from.
    
    Returns:
        str -- The last line from a ascii file.
    """

    # Reopen the file in untranslated newline mode to let us work with UNIX and DOS style line endings.
    with open(file = f if isinstance(f, str) else f.name, newline = '', mode = 'r') as f:
        # Jump to the last character of the file.
        f.seek(0, os.SEEK_END)
        f.seek(f.tell() - 1, os.SEEK_SET)

        # Move the read pointer back until we reach the end of the last line.
        while f.read(1) == '\n':
            f.seek(f.tell() - 2, os.SEEK_SET)

        # Handle DOS CRLF line endings by moving back an additional character if necessary.
        f.seek(f.tell() - 1, os.SEEK_SET)
        if f.read(1) == '\r':
            f.seek(f.tell() - 2, os.SEEK_SET)
        else:
            f.seek(f.tell() - 1, os.SEEK_SET)

        # Move back until we hit the start of the last line in the file.
        while f.read(1) != '\n':
            f.seek(f.tell() - 2, os.SEEK_SET)
        return f.readline()

def huffmanDecode(string, options):
    for option in options:
        if re.match(r'^' + option, string):
            return option

def expMovingAvg(nums, alpha, idx = 0):
    # Base case. Return the number itself.
    if idx == len(nums) - 1:
        return nums[idx]

    # Recursive case. 
    return alpha * nums[idx] + (1 - alpha) * expMovingAvg(nums, alpha, idx + 1)

def clamp(num, minNum, maxNum):
    return max(min(num, maxNum), minNum)