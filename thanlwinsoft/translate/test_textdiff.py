#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Keith Stribley http://www.thanlwinsoft.org/ 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from thanlwinsoft.translate.textdiff import Match
import thanlwinsoft.translate.textdiff
import difflib
import sys

def test_blocks() :
    a = u"Find the common blocks using the difflib package."
    b = u"Find the common blocks using the textdiff package from thanlwinsoft."
    run_test(None, a, b)

def test_unicode_marks() :
    a =u"ဥပမာ။ ကာမှန်လား။"
    b =u"ဥပမာ။ ကောင်းမှန်လား။"
    textdiff = thanlwinsoft.translate.textdiff.SequenceMatcher(None, a, b)
    textdiff_matches = textdiff.get_matching_blocks()
    sys.stderr.write( str(textdiff_matches) + "\n")
    expected = [(0, 0, 6), (8, 12, 8), (len(a), len(b), 0)]
    assert(textdiff_matches == expected)

def test_unicode_with_junk() :
    a =u" ဥပမာ။ ကာမှန်လား။\t              "
    b =u"ဥပမာ။ကောင်းမှန်လား။ "
    #textdiff = thanlwinsoft.translate.textdiff.SequenceMatcher(lambda x : x in " \t", a, b)
    textdiff = thanlwinsoft.translate.textdiff.SequenceMatcher(None, a, b)
    textdiff_matches = textdiff.get_matching_blocks()
    sys.stderr.write( str(textdiff_matches) + "\n")
    # the space at the end could legitimately match just after the tab as well
    expected = [Match(1, 0, 5), Match(9, 11, 8), Match(31, 19, 1), Match(len(a), len(b), 0)]
    assert(textdiff_matches == expected)

def run_test(junk, a, b) :
    difflibmatcher = difflib.SequenceMatcher(junk, a, b)
    textdiff = thanlwinsoft.translate.textdiff.SequenceMatcher(junk, a, b)
    textdiff_matches = textdiff.get_matching_blocks()
    difflib_matches = difflibmatcher.get_matching_blocks()
    textdiff_match_len = 0
    difflib_match_len = 0
    sys.stderr.write( str(textdiff_matches) + "\n")
    sys.stderr.write( str(difflib_matches) + "\n")
    for block in textdiff_matches :
        textdiff_match_len += block[2]
    for block in difflib_matches :
        difflib_match_len += block[2]
    assert(textdiff_match_len == difflib_match_len)
#    if (difflibmatcher.get_matching_blocks() != textdiff.get_matching_blocks()) :
#        thanlwinsoft.translate.textdiff.markup_deltas(a, b, difflibmatcher.get_matching_blocks())
#        thanlwinsoft.translate.textdiff.markup_deltas(a, b, textdiff.get_matching_blocks())
#    assert(difflibmatcher.get_matching_blocks() == textdiff.get_matching_blocks())
    return [textdiff_matches, difflib_matches]

