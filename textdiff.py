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
import unicodedata
import random
import time

def is_mark(c) :
    cat = unicodedata.category(c)
    return cat[0] == 'M'

def next_cluster(text, offset) :
    i = offset + 1
    text_len = len(text)
    while (i < text_len and is_mark(text[i])) :
        i += 1
    return text[offset:i]

def prev_cluster(text, offset) :
    i = offset - 1
    while (i >= 0 and is_mark(text[i])) :
        i -= 1
    return text[i:offset]

def find_matches(a, b) :
    start = 0
    ca = next_cluster(a, start)
    cb = next_cluster(b,start)
    while (start < len(a) and start < len(b) and ca == cb):
        start += len(ca)
        ca = next_cluster(a, start)
        cb = next_cluster(b, start)
    a_end = len(a)
    b_end = len(b)
    ca = prev_cluster(a, a_end)
    cb = prev_cluster(b, b_end)
    while (a_end > start and b_end > start and ca == cb):
        a_end -= len(ca)
        b_end -= len(cb)
        ca = prev_cluster(a, a_end)
        cb = prev_cluster(b, b_end)
    if (a_end < start) : a_end = a_start
    if (b_end < start) : b_end = b_start
    lcs_data = longest_common_subsequence(a, b, start, start, a_end, b_end)
#    print lcs_data.lcs
    common = []
    if (start > 0) : common.append((0, 0, start))
    if (lcs_data.lcs[-1][-1] > 0) :
        common.extend(get_a_longest_subsequence(a, b, lcs_data))
    if (a_end < len(a)) : common.append((a_end, b_end, len(a) - a_end))
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
                    common.insert(0, (lcs_data.a_clusters[row-1], lcs_data.b_clusters[col-1], lcs_data.a_clusters[row] - lcs_data.a_clusters[row-1]))
                    row -= 1
                    col -= 1

    return common

class LcsData :
    a_clusters= []
    b_clusters = []
    lcs = [[0]]

def longest_common_subsequence(a, b, a_offset, b_offset, a_end, b_end) :
#    lcs[0:a_end - a_offset + 1][0:b_end - b_offset + 1] = 0
    lcs = [[0] ] 
    data = LcsData()
    data.a_clusters = []
    a_pos = a_offset
    b_pos = b_offset
    i = 1
    while a_pos < a_end :
        data.a_clusters.append(a_pos)
        a_cluster = next_cluster(a, a_pos)
        a_pos += len(a_cluster)
        lcs.append([0])
        i+= 1
    data.a_clusters.append(a_pos)
    i = 1
    while b_pos < b_end :
        data.b_clusters.append(b_pos)
        b_cluster = next_cluster(b, b_pos)
        b_pos += len(b_cluster)
        lcs[0].append(0)
        i+= 1
    data.b_clusters.append(b_pos)

    a_pos = a_offset
    for r in range(1, a_end - a_offset + 1) :
        b_pos = b_offset
        a_cluster = next_cluster(a, a_pos)
        for c in range(1, b_end - b_offset + 1) :
            b_cluster = next_cluster(b, b_pos)
            if (a_cluster == b_cluster) :
                lcs[r].append(lcs[r-1][c-1] + 1)
            else :
                lcs[r].append(max(lcs[r-1][c], lcs[r][c-1]))
            b_pos += len(b_cluster)
            if b_pos == len(b): break;
        a_pos += len(a_cluster)
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


if __name__ == "__main__":
    if (len(sys.argv) >= 3) :
        a = unicode(sys.argv[1], 'utf-8')
        b = unicode(sys.argv[2], 'utf-8')
        matches = find_matches(a, b)
        print matches
        print markup_deltas(a, b, matches)
    else :
        if (len(sys.argv) == 2) : 
            if (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
                print "Usage: " + sys.argv[0] + " textA textB"
            if (sys.argv[1] == '--stats') :
                do_stats(100)

