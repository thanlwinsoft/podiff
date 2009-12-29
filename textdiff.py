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

def find_matches(a, b, min_match=1):
	"""Find the segments of text which are common between a and b.

The common segments are given as a list of tupples: (aOffset, bOffset, length)
min_match can be used to speed up the search but will not show areas with less than min_match
characters in common."""
	a_len = len(a)
	b_len = len(b)
	cf = []
	divisor = 10
	first_pass_min = int(min(len(a),len(b)) / divisor)
	if (first_pass_min < 1): first_pass_min = 1
	matches = find_match_lists(a, b, 0, 0, 0, first_pass_min)
	print matches
	while (first_pass_min > min_match) :
		divisor *= 5
		first_pass_min = int(min(len(a),len(b)) / divisor)
		if (first_pass_min < 1): first_pass_min = 1
		matches = find_match_lists(a, b, 0, 0, matches[0], first_pass_min)
		print matches
	mList = matches
	while (len(mList) > 1) :
		cf.append(mList[1][0])
		mList = mList[1][1]
	return cf
	
def find_match(a, b, aStart, bStart, min_match=1):
	"""Find a match common to a and b starting at aStart, bStart"""
	match_len = min_match 
	aPos = aStart
#	print aStart, bStart
	bOffset = b.find(a[aPos:aPos+match_len], bStart)
	while (bOffset == -1) :
		aPos += 1
		if (aPos+match_len > len(a)) : return None
		bOffset = b.find(a[aPos:aPos+match_len], bStart)
	# found a match, now see how much it can be extended
	while (aPos+match_len < len(a) and bOffset+match_len < len(b) and
			a[aPos+match_len] == b[bOffset+match_len]) : match_len += 1
	return (aPos, bOffset, match_len)

def find_match_lists(a, b, aStart, bStart, min_combined, min_match=1):
	"""Create a tree of possible matches.
Returns a list, first element is length of longest match
next element contains list of tupples of best match.
"""
	matches = [0]
	i = 0
	longest_match = min_combined
	longest_index = -1
	while (aStart+min_match < len(a)):
		match = find_match(a, b, aStart, bStart, min_match)
		if (match is not None):
			# if there is less than longest match left in b, then this path can't be the best
			if (len(b) - match[1] < longest_match) :
				aStart+=1
				continue
			min_combined_match = longest_match - match[2]
			if (min_combined_match < 0) :
				min_combined_match = 0
			i+= 1
			match_list = find_match_lists(a, b, match[0] + match[2], match[1] + match[2], min_combined_match, min_match)
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
		if (len(sys.argv) >= 4) : min_match = int(sys.argv[3])
#		print find_matches(sys.argv[1], sys.argv[2], 0, 0, min_match)
		common = find_matches(sys.argv[1], sys.argv[2], min_match)
		print common
		out = markup_deltas(sys.argv[1], sys.argv[2], common)
		print out[0], '\n', out[1]


