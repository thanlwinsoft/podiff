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

from thanlwinsoft.translate.podiff import PODiff

expectedPoDiffResults = {}

class TestPoDiff(PODiff) :
    def __init__(self) :
        PODiff.__init__(self)
        self.podiff = PODiff()
        self.fileBase = "testBase.po"
        self.fileA = "testA.po"
        self.fileB = "testB.po"
        self.fileMerge = "testMerge.po"
    def set_diff_titles(self, a, b):
        assert(a == self.fileA)
        assert(b == self.fileB)
    def set_merge_titles(self, base, a, b, merge) :
        assert(base == self.fileBase)
        assert(merge == self.fileMerge)
        assert(a == self.fileA)
        assert(b == self.fileB)
        
    def on_dirty(self) :
        assert(self.dirty[0] == False)
        assert(self.dirty[1] == False)
        assert(self.dirty[2] == False)
        if (self.test == "Merge") :
            assert(self.dirty[3] == True)

    def show_side(self, side, row, index, unit, cf_unit, modified, state, plural) :
        pass
    def test_diff(self):
        self.test = "Diff"
        self.diff(self.fileA, self.fileB)

    def test_merge(self):
        self.test = "Merge"
        self.merge(self.fileBase, self.fileA, self.fileB, self.fileMerge)
    
    def set_total_units(self, row_count) :
        self.unit_count = row_count
#        assert(row_count == 25)


