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

import sys
import math
import unicodedata

def find_matches(a, b, min_match=0):
	"""Find the segments of text which are common between a and b.

The common segments are given as a list of tupples: (aOffset, b_offset, length)
min_match can be used to speed up the search but will not show areas with less than min_match
characters in common."""
	mdict = dict()
	cf = []
	if (min_match == 0) :
		min_match = min(len(a), len(b))/10
	matches = find_match_lists(a, b, 0, 0, mdict, min_match)
	mList = matches
	while (len(mList) > 1) :
		cf.append(mList[1][0])
		mList = mList[1][1]
	return cf
	
def is_mark(c) :
	cat = unicodedata.category(c)
	return cat[0] == 'M'

def find_cluster_bounds(a, i, j) :
	# move start to a non-mark
	while(i < len(a) and is_mark(a[i])):
		i+= 1
	if (j <= i): j = i + 1
	while (j < len(a) and is_mark(a[j])):
		j+= 1
	return (i, j)

def find_match(a, b, aStart, bStart, min_match=1):
	"""Find a match common to a and b starting at aStart, bStart"""
	match_len = min_match 
	a_pos = aStart
	a_end = min(a_pos + match_len, len(a))
#	print aStart, bStart
	(a_pos, a_end) = find_cluster_bounds(a, a_pos, a_end)
	if (a_pos >= len(a)): return None
	b_offset = b.find(a[a_pos:a_end], bStart)
	while (b_offset == -1) :
		a_pos += 1
		a_end = min(a_pos + match_len, len(a))
		(a_pos, a_end) = find_cluster_bounds(a, a_pos, a_end)
		if (a_pos >= len(a)) : return None
		b_offset = b.find(a[a_pos:a_end], bStart)
	# found a match, now see how much it can be extended
	while (a_pos+match_len < len(a) and b_offset+match_len < len(b) and
			a[a_pos+match_len] == b[b_offset+match_len]) :
		if (not is_mark(a[a_pos+match_len])) : a_end = a_pos+match_len
		match_len += 1
	# check we haven't stopped mid-cluster
	if ((a_pos+match_len < len(a) and is_mark(a[a_pos+match_len])) or
		(b_offset+match_len < len(b) and is_mark(b[b_offset+match_len]))):
		match_len = a_end - a_pos
	return (a_pos, b_offset, match_len)

def find_match_lists(a, b, aStart, bStart, mdict, min_match=1):
	"""Create a tree of possible matches.
Returns a list, first element is length of longest match
next element contains list of tupples of best match.
"""
	matches = [0]
	i = 0
	longest_match = 0
	longest_index = -1
	while (aStart+min_match < len(a)):
		match = find_match(a, b, aStart, bStart, min_match)
		if (match is not None):
			# if there is less than longest match left in b, then this path can't be the best
			if (len(b) - match[1] < longest_match) :
				aStart+=1
				continue
			i+= 1
			aOffset = match[0] + match[2]
			b_offset = match[1] + match[2]
			key = (aOffset, b_offset)
			if key in dict(mdict):
				match_list = mdict[key]
			else:
				match_list = find_match_lists(a, b, aOffset, b_offset, mdict, min_match)
				mdict[key] = match_list
			matches.append([match, match_list])
			combined_match_len = match[2] + matches[i][1][0]
			if combined_match_len > longest_match : 
				longest_index = i
				longest_match = combined_match_len
		aStart+= 1
	matches[0] = longest_match
	if longest_index > -1: matches[1] = matches[longest_index]
	matches = matches[0:2]
	return matches

def delta_str(a, b, delta_prefix='[', delta_suffix=']', min_match=3) :
	"""Compares two strings and marks up the areas which are different with specified characters"""
	common = find_deltas(sys.argv[1], sys.argv[2], min_match)
	return markup_delta(a, b, common, delta_prefix, delta_suffix)
	
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
		min_match = 1
		a = unicode(sys.argv[1], 'utf-8')
		b = unicode(sys.argv[2], 'utf-8')
		assert(isinstance(a, unicode))
		assert(isinstance(b, unicode))		
		if (len(sys.argv) >= 4) : min_match = int(sys.argv[3])
#		print find_matches(sys.argv[1], sys.argv[2], 0, 0, min_match)
		common = find_matches(a, b, min_match)
		print common
		out = markup_deltas(a, b, common)
		print out[0], '\n', out[1]


