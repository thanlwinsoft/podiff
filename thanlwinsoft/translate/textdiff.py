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
#
# The algorithm used here is based on the description at:
# http://en.wikipedia.org/wiki/Longest_common_subsequence_problem

import sys
import math
import collections
import unicodedata
import random
import time

Match  = collections.namedtuple("Match", "a b size")

def is_mark(c) :
    cat = unicodedata.category(c)
    return cat[0] == 'M'

def next_cluster(text, offset) :
    text_len = len(text)
    start = offset
    i = start + 1
    while (i < text_len and is_mark(text[i])) :
        i += 1
    return [text[start:i], i - offset]

def prev_cluster(text, offset) :
    last = offset
    i = last - 1
    while (i >= 0 and is_mark(text[i])) :
        i -= 1
    return [text[i:last], offset - i]

def find_matches(a, b) :
    start_a = 0
    start_b = 0
    ca, ca_len = next_cluster(a, start_a)
    cb, cb_len = next_cluster(b,start_b)
    while (start_a < len(a) and start_b < len(b) and ca == cb):
        start_a += ca_len
        start_b += cb_len
        ca, ca_len = next_cluster(a, start_a)
        cb, cb_len = next_cluster(b, start_b)
    a_end = len(a)
    b_end = len(b)
    ca, ca_len = prev_cluster(a, a_end)
    cb, cb_len = prev_cluster(b, b_end)
    while (a_end > start_a and b_end > start_b and ca == cb):
        a_end -= ca_len
        b_end -= cb_len
        ca, ca_len = prev_cluster(a, a_end)
        cb, cb_len = prev_cluster(b, b_end)
    if (a_end < start_a) : a_end = start_a
    if (b_end < start_b) : b_end = start_b
    lcs_data = longest_common_subsequence(a, b, start_a, start_b, a_end, b_end)
#    print lcs_data.lcs
    common = []
    if (start_a > 0 and start_b > 0) : common.append(Match(0, 0, min(start_a, start_b) ))
    if (lcs_data.lcs[-1][-1] > 0) :
        common.extend(get_a_longest_subsequence(a, b, lcs_data))
    if (a_end < len(a)) : common.append(Match(a_end, b_end, len(a) - a_end))
    return common

def get_a_longest_subsequence(a, b, lcs_data) :
    a_cluster_len = len(lcs_data.lcs)
    b_cluster_len = len(lcs_data.lcs[0])
    col = b_cluster_len - 1
    row = a_cluster_len - 1
    common = []
    while row > 0 and col > 0 :
        if (lcs_data.lcs[row][col-1] == lcs_data.lcs[row][col]) :
                col -= 1
        else :
            if (lcs_data.lcs[row-1][col] == lcs_data.lcs[row][col]) :
                row -= 1
            else :
                if (lcs_data.lcs[row-1][col-1] < lcs_data.lcs[row][col]) :
                    a_start = lcs_data.a_clusters[row-1]
                    b_start = lcs_data.b_clusters[col-1]
                    length = lcs_data.a_clusters[row] - lcs_data.a_clusters[row-1]
                    # merge ajacent runs
                    if (len(common) > 0) and (common[0][0] == a_start + length) and (common[0][1] == b_start + length) :
                        length += common[0][2]
                        common[0] = Match(a_start, b_start, length)
                    else :
                        common.insert(0, Match(a_start, b_start, length))
                    row -= 1
                    col -= 1

    return common

class LcsData :
    a_clusters= []
    b_clusters = []
    lcs = [[0]]

def longest_common_subsequence(a, b, a_offset, b_offset, a_end, b_end) :
#    lcs[0:a_end - a_offset + 1][0:b_end - b_offset + 1] = 0
    #print u'"{0}" "{1}"'.format(a,b)
    lcs = [[0] ] 
    data = LcsData()
    data.a_clusters = []
    data.b_clusters = []
    a_pos = a_offset
    b_pos = b_offset
    i = 1
    while a_pos < a_end :
        data.a_clusters.append(a_pos)
        a_cluster, a_len = next_cluster(a, a_pos)
        a_pos += a_len
        lcs.append([0])
        i+= 1
    data.a_clusters.append(a_pos)
    i = 1
    while b_pos < b_end :
        data.b_clusters.append(b_pos)
        b_cluster, b_len = next_cluster(b, b_pos)
        b_pos += b_len
        lcs[0].append(0)
        i+= 1
    data.b_clusters.append(b_pos)
    #print len(lcs[0]), b_end - b_offset, len(data.b_clusters)

    a_pos = a_offset
    for r in range(1, len(data.a_clusters)) :
        b_pos = b_offset
        a_cluster, a_len = next_cluster(a, a_pos)
        for c in range(1, len(data.b_clusters)) :
            b_cluster, b_len = next_cluster(b, b_pos)
            # print c, len(lcs[r-1])
            assert(c < len(lcs[r-1]))
            assert(r < len(lcs))
            if (a_cluster == b_cluster) :
                lcs[r].append(lcs[r-1][c-1] + 1)
            else :
                lcs[r].append(max(lcs[r-1][c], lcs[r][c-1]))
            b_pos += b_len
            if b_pos == len(b): break;
        a_pos += a_len
        if a_pos == len(a): break;
    data.lcs = lcs
    return data

def do_stats(length) :
    alphabet = u"abcdefghijklmnopqrstuvwxyz"
#    print a,b
    times = []
    elapsed = 0
    for i in range(1000) :
        a = ""
        b = ""
        for i in range(length) :
            a += random.choice(alphabet)
            b += random.choice(alphabet)
        start = time.clock()
        find_matches(a,b)
        end = time.clock()
        elapsed = end - start
        times.append(elapsed)
    print "min ", min(times), ", avg " , sum(times)/len(times), ", max ", max(times)

def markup_deltas(a, b, common, delta_prefix='[', delta_suffix=']') :
    """Uses the result of find_deltas and marks up the areas which are different with specified characters"""
    marked_a = ""
    marked_b = ""
    aPos = 0
    bPos = 0
    for i in range(len(common)) :
        if (aPos < common[i][0]) :
            marked_a += delta_prefix + a[aPos:common[i][0]] + delta_suffix
        if (bPos < common[i][1]) :
            marked_b += delta_prefix + b[bPos:common[i][1]] + delta_suffix
        aPos = common[i][0] + common[i][2]
        bPos = common[i][1] + common[i][2]
        marked_a += a[common[i][0]:aPos]
        marked_b += b[common[i][1]:bPos]
    if (aPos < len(a)) :
        marked_a += delta_prefix + a[aPos:len(a)] + delta_suffix
    if (bPos < len(b)) :
        marked_b += delta_prefix + b[bPos:len(b)] + delta_suffix
    return (marked_a, marked_b)

class SequenceMatcher :
    """SequenceMatcher interface to textdiff. Only a subset of the difflib methods are supported. """
    def __init__(self, junk=None, a=None, b=None) :
        self.junk = junk
        self.a = a
        self.b = b
        self.matches = None
    def set_seqs(self, a,b) :
        self.a = a
        self.b = b
        self.matches = None
    def set_seq1(self, a) :
        self.a = a
        self.matches = None
    def set_seq2(self, b) :
        self.b = b
        self.matches = None
    def get_matching_blocks(self) :
        if self.matches is None:
            self.matches = find_matches(self.a, self.b)
            if len(self.matches) == 0 or self.matches[len(self.matches)-1][0] < len(self.a) or self.matches[len(self.matches)-1][1] < len(self.b) :
                self.matches.append( Match(len(self.a), len(self.b), 0) )
        return self.matches


if __name__ == "__main__":
    if (len(sys.argv) >= 3) :
        a = unicode(sys.argv[1], 'utf-8')
        b = unicode(sys.argv[2], 'utf-8')
#        matches = find_matches(a, b)
        matcher = SequenceMatcher(None, a, b)
        matches = matcher.get_matching_blocks()
        print matches
        print markup_deltas(a, b, matches)
    else :
        if (len(sys.argv) == 2) : 
            if (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
                print "Usage: " + sys.argv[0] + " textA textB"
            if (sys.argv[1] == '--stats') :
                do_stats(100)

