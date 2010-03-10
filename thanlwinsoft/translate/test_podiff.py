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

from thanlwinsoft.translate.podiff import PoDiff
from thanlwinsoft.translate.podiff import Side
from thanlwinsoft.translate.podiff import UnitState
import collections
import sys

DiffResult = collections.namedtuple("DiffResult", "left right plural state")
MergeResult = collections.namedtuple("MergeResult", "base left right plural state")

# 1,4, 6, 7, are unchanged, as are single 22, 23, 24, 25
expectedPoDiffResults = {
    u"test2 modify in A" : DiffResult(True, True, 0, 0x100),
    u"test3 modify in B" : DiffResult(True, True, 0, 0x100),
    u"test4 modify in A & B" : DiffResult(True, True, 0, 0x100),
    u"test8 move in A, modify in A" : DiffResult(True, True, 0, 0x100),
    u"test9 move in B, modify in B" : DiffResult(True, True, 0, 0x100),
    u"test10 move and modify in A and B" : DiffResult(True, True, 0, 0x100),
    u"test11 new in A" : DiffResult(True, False, 0, 0x100),
    u"test12 new in B" : DiffResult(False, True, 0, 0x100),
    u"test13 new in A and B" : DiffResult(True, True, 0, 0x100),
    u"test15 removed in A" : DiffResult(False, True, 0, 0x100),
    u"test16 removed in B" : DiffResult(True, False, 0, 0x100),
    u"test17 removed in A, modified in B" : DiffResult(False, True, 0, 0x100),
    u"test18 removed in B, modified in A" : DiffResult(True, False, 0, 0x100),
    u"test19 with context" : DiffResult(True, True, 0, 0x100),
    (u"test19 with context", u"modify in A") : DiffResult(True, True, 0, 0x100),
    (u"test19 with context", u"modify in B") : DiffResult(True, True, 0, 0x100),
    (u"test19 with context", u"modify in both") : DiffResult(True, True, 0, 0x100),
    u"test20 single" : DiffResult(True, True, 0, 0x100),
    u"test20 plural" : DiffResult(True, True, 1, 0x100),
    u"test21 single" : DiffResult(True, True, 0, 0x100),
    u"test21 plural" : DiffResult(True, True, 1, 0x100),
    u"test22 plural" : DiffResult(True, True, 1, 0x100),
    u"test23 plural" : DiffResult(True, False, 1, 0x100),
    u"test24 plural" : DiffResult(False, True, 1, 0x100),
    u"test25 plural" : DiffResult(True, True, 1, 0x100),
    u"test27 single change in both" : DiffResult(True, True, 0, 0x100),
    u"test27 plural change in both" : DiffResult(True, True, 1, 0x100)
}

expectedPoMergeResults = {
# 1 is unchanged
    u"test2 modify in A" : MergeResult(True, True, True, 0, 0x205),
    u"test3 modify in B" : MergeResult(True, True, True, 0, 0x209),
    u"test4 modify in A & B" : MergeResult(True, True, True, 0, 0x202),
# 5 is unchanged
#    u"test6 move in A" : MergeResult(True, True, True, 0, 0x200),
#    u"test7 move in B" : MergeResult(True, True, True, 0, 0x200),
    u"test8 move in A, modify in A" : MergeResult(True, True, True, 0, 0x205),
    u"test9 move in B, modify in B" : MergeResult(True, True, True, 0, 0x209),
    u"test10 move and modify in A and B" : MergeResult(True, True, True, 0, 0x202),
    u"test11 new in A" : MergeResult(False, True, False, 0, 0x205),
    u"test12 new in B" : MergeResult(False, False, True, 0, 0x209),
    u"test13 new in A and B" : MergeResult(True, True, True, 0, 0x202),
    u"test14 removed in A and B" : MergeResult(True, False, False, 0, 0x201),
    u"test15 removed in A" : MergeResult(True, False, True, 0, 0x205),
    u"test16 removed in B" : MergeResult(True, True, False, 0, 0x209),
    u"test17 removed in A, modified in B" : MergeResult(True, False, True, 0, 0x202),
    u"test18 removed in B, modified in A" : MergeResult(True, True, False, 0, 0x202),
    u"test19 with context" : MergeResult(True, True, True, 0, 0x202),
    (u"test19 with context", u"modify in A") : MergeResult(True, True, True, 0, 0x205),
    (u"test19 with context", u"modify in B") : MergeResult(True, True, True, 0, 0x209),
    (u"test19 with context", u"modify in both") : MergeResult(True, True, True, 0, 0x202),
    u"test20 single" : MergeResult(True, True, True, 0, 0x205),
    u"test20 plural" : MergeResult(True, True, True, 1, 0x209),
    u"test21 single" : MergeResult(True, True, True, 0, 0x209),
    u"test21 plural" : MergeResult(True, True, True, 1, 0x205),
#    u"test22 single" : MergeResult(True, True, True, 0, 0x200),
    u"test22 plural" : MergeResult(True, True, True, 1, 0x202),
#    u"test23 single only" : MergeResult(True, True, True, 0, 0x200),
    u"test23 plural" : MergeResult(True, True, False, 1, 0x205),
#    u"test24 single only" : MergeResult(True, True, True, 0, 0x200),
    u"test24 plural" : MergeResult(True, False, True, 1, 0x209),
    u"test25 plural" : MergeResult(True, True, True, 1, 0x202),
    u"test26 - very very very very very very very very very very very very very very very very very  long" : MergeResult(True, False, False, 0, 0x201),
    u"test27 single change in both" : MergeResult(True, True, True, 0, 0x202),
    u"test27 plural change in both" : MergeResult(True, True, True, 1, 0x202),
}

expectedMergeResults = {
    u"test4 modify in A & B" : MergeResult(True, True, True, 0, 0x201),
    u"test27 single change in both" : MergeResult(True, True, True, 0, 0x201),
    u"test27 plural change in both" : MergeResult(True, True, True, 1, 0x201),
}

expectedXliffDiffResults = {
    u"test2 modify in A" : DiffResult(True, True, 0, 0x100),
    u"test3 modify in B" : DiffResult(True, True, 0, 0x100),
    u"test4 modify in A & B" : DiffResult(True, True, 0, 0x100),
    u"test8 move in A, modify in A" : DiffResult(True, True, 0, 0x100),
    u"test9 move in B, modify in B" : DiffResult(True, True, 0, 0x100),
    u"test10 move and modify in A and B" : DiffResult(True, True, 0, 0x100),
    u"test11 new in A" : DiffResult(True, False, 0, 0x100),
    u"test12 new in B" : DiffResult(False, True, 0, 0x100),
    u"test13 new in A and B" : DiffResult(True, True, 0, 0x100),
    u"test15 removed in A" : DiffResult(False, True, 0, 0x100),
    u"test16 removed in B" : DiffResult(True, False, 0, 0x100),
    u"test17 removed in A, modified in B" : DiffResult(False, True, 0, 0x100),
    u"test18 removed in B, modified in A" : DiffResult(True, False, 0, 0x100),
    u"test19 with context" : DiffResult(True, True, 0, 0x100),
    u"test20 single" : DiffResult(True, True, 0, 0x100),
    u"test20 plural" : DiffResult(True, True, 1, 0x100),
    u"test21 single" : DiffResult(True, True, 0, 0x100),
    u"test21 plural" : DiffResult(True, True, 1, 0x100),
    u"test22 plural" : DiffResult(True, True, 1, 0x100),
    u"test23 plural" : DiffResult(True, False, 1, 0x100),
    u"test24 plural" : DiffResult(False, True, 1, 0x100),
    u"test25 plural" : DiffResult(True, True, 1, 0x100)
}

expectedXliffMergeResults = {
# 1 is unchanged
    u"test2 modify in A" : MergeResult(True, True, True, 0, 0x205),
    u"test3 modify in B" : MergeResult(True, True, True, 0, 0x209),
    u"test4 modify in A & B" : MergeResult(True, True, True, 0, 0x202),
# 5 is unchanged
#    u"test6 move in A" : MergeResult(True, True, True, 0, 0x200),
#    u"test7 move in B" : MergeResult(True, True, True, 0, 0x200),
    u"test8 move in A, modify in A" : MergeResult(True, True, True, 0, 0x205),
    u"test9 move in B, modify in B" : MergeResult(True, True, True, 0, 0x209),
    u"test10 move and modify in A and B" : MergeResult(True, True, True, 0, 0x202),
    u"test11 new in A" : MergeResult(False, True, False, 0, 0x205),
    u"test12 new in B" : MergeResult(False, False, True, 0, 0x209),
    u"test13 new in A and B" : MergeResult(True, True, True, 0, 0x202),
    u"test14 removed in A and B" : MergeResult(True, False, False, 0, 0x201),
    u"test15 removed in A" : MergeResult(True, False, True, 0, 0x205),
    u"test16 removed in B" : MergeResult(True, True, False, 0, 0x209),
    u"test17 removed in A, modified in B" : MergeResult(True, False, True, 0, 0x202),
    u"test18 removed in B, modified in A" : MergeResult(True, True, False, 0, 0x202),
    u"test19 with context" : MergeResult(True, True, True, 0, 0x202),
    u"test20 single" : MergeResult(True, True, True, 0, 0x205),
    u"test20 plural" : MergeResult(True, True, True, 1, 0x209),
    u"test21 single" : MergeResult(True, True, True, 0, 0x209),
    u"test21 plural" : MergeResult(True, True, True, 1, 0x205),
#    u"test22 single" : MergeResult(True, True, True, 0, 0x200),
    u"test22 plural" : MergeResult(True, True, True, 1, 0x202),
#    u"test23 single only" : MergeResult(True, True, True, 0, 0x200),
    u"test23 plural" : MergeResult(True, True, False, 1, 0x205),
#    u"test24 single only" : MergeResult(True, True, True, 0, 0x200),
    u"test24 plural" : MergeResult(True, False, True, 1, 0x209),
#    u"test25 single only" : MergeResult(True, True, True, 0, 0x200),
    u"test25 plural" : MergeResult(True, True, True, 1, 0x202),
    u"test26 - very very very very very very very very very very very very very very very very very  long" : MergeResult(True, False, False, 0, 0x201),
}

class TestPoDiff(PoDiff) :
    def __init__(self) :
        PoDiff.__init__(self)
        self.fileBase = "testBase.po"
        self.fileA = "testA.po"
        self.fileB = "testB.po"
        self.fileMerge = "testMerge.po"
        self.expected_results = None
    def set_diff_titles(self, a, b):
        assert(a == self.fileA or a == self.fileA.replace(".po", ".xlf"))
        assert(b == self.fileB or b == self.fileB.replace(".po", ".xlf"))
    def set_merge_titles(self, base, a, b, merge) :
        assert(base == self.fileBase or base == self.fileBase.replace(".po", ".xlf"))
        assert(merge == self.fileMerge or merge == self.fileMerge.replace(".po", ".xlf"))
        assert(a == self.fileA or a == self.fileA.replace(".po", ".xlf"))
        assert(b == self.fileB or b == self.fileB.replace(".po", ".xlf"))
        
    def on_dirty(self) :
        assert(self.dirty[0] == False)
        assert(self.dirty[1] == False)
        assert(self.dirty[2] == False)
        if (self.test == "Merge") :
            assert(self.dirty[3] == True)

    def show_side(self, side, row, index, unit, cf_unit, modified, state, plural) :
        sys.stderr.write("ID:[{0}] Side {1} Plural {2} State {3}\n".format(unit.getid(), side, plural, state))
        if (plural == 0) :
            test_key = unicode(unit.source)
        else :
            assert(unit.hasplural())
            test_key = unicode(unit.source.strings[1])
        if unit.getcontext() is not None and len(unit.getcontext()) > 0:
            test_key = (test_key, unit.getcontext())
        assert (test_key in self.expected_results)                    
        expected = self.expected_results[test_key]
        assert(plural == expected.plural)
        assert(state == expected.state)
        if self.test == "Diff" :
            if (side == Side.LEFT) :
                assert(expected.left)
            else :
                if (side == Side.RIGHT) :
                    assert(expected.right)
                else :
                    assert(False)
            assert(state == UnitState.MODE_DIFF)
        else :
            if (side < Side.MERGE) :
                assert(expected[side])
            assert(state & UnitState.MODE_MERGE)

    def test_diff(self):
        """Test comparsion between 2 files"""
        self.test = "Diff"
        self.expected_results = expectedPoDiffResults
        self.diff(self.fileA, self.fileB)
        self.expected_results = None

    def test_merge(self):
        """Test merging 2 files modified from a common base"""
        self.test = "Merge"
        self.expected_results = expectedPoMergeResults
        self.merge(self.fileBase, self.fileA, self.fileB, self.fileMerge)
        self.expected_results = None

    def test_merge_from(self):
        """Test merge from when selecting an one of the alternative translations."""
        assert(self.stores[Side.LEFT] is not None)
        assert(self.stores[Side.RIGHT] is not None)
        assert(self.stores[Side.BASE] is not None)
        assert(self.stores[Side.MERGE] is not None)
        self.expected_results = expectedMergeResults
        from_row = -1 # not needed currently, except for show_side call back
        unit_index = -1 # not needed currently, except for show_side call back
        #test a single entry
        plural = 0
        test_id = "test4 modify in A & B"
        a_unit = self.stores[Side.LEFT].findid(test_id)
        b_unit = self.stores[Side.RIGHT].findid(test_id)
        # resolve using a
        self.merge_from(Side.LEFT, from_row, unit_index, a_unit, plural)
        base_unit = self.stores[Side.BASE].findid(test_id)
        result = self.stores[Side.MERGE].findid(test_id)
        assert(unicode(a_unit.gettarget()) == unicode(result.gettarget()))
        assert(unicode(b_unit.gettarget()) != unicode(result.gettarget()))
        assert(unicode(base_unit.gettarget()) != unicode(result.gettarget()))
        # resolve using b instead
        self.merge_from(Side.RIGHT, from_row, unit_index, b_unit, plural)
        base_unit = self.stores[Side.BASE].findid(test_id)
        assert(unicode(b_unit.gettarget()) == unicode(result.gettarget()))
        assert(unicode(a_unit.gettarget()) != unicode(result.gettarget()))
        assert(unicode(base_unit.gettarget()) != unicode(result.gettarget()))
        # revert to base
        self.merge_from(Side.BASE, from_row, unit_index, base_unit, plural)
        assert(unicode(a_unit.gettarget()) != unicode(result.gettarget()))
        assert(unicode(b_unit.gettarget()) != unicode(result.gettarget()))
        assert(unicode(base_unit.gettarget()) == unicode(result.gettarget()))

        # test a plural entry
        test_id = "test27 single change in both"#test27 plural change in both"
        a_unit = self.stores[Side.LEFT].findid(test_id)
        b_unit = self.stores[Side.RIGHT].findid(test_id)
        # single from a, single from b
        self.merge_from(Side.LEFT, from_row, unit_index, a_unit, 0)
        self.merge_from(Side.RIGHT, from_row, unit_index, b_unit, 1)
        result = self.stores[Side.MERGE].findid(test_id)
        assert(unicode(a_unit.gettarget()) == unicode(result.gettarget()))
        assert(unicode(b_unit.gettarget()) != unicode(result.gettarget()))
        assert(unicode(a_unit.gettarget().strings[1]) != unicode(result.gettarget().strings[1]))
        assert(unicode(b_unit.gettarget().strings[1]) == unicode(result.gettarget().strings[1]))
        self.expected_results = None

    def test_xliff_diff(self):
        """Test comparsion between 2 files"""
        self.test = "Diff"
        self.expected_results = expectedXliffDiffResults
        self.diff(self.fileA.replace(".po", ".xlf"), self.fileB.replace(".po", ".xlf"))
        self.expected_results = None

    def test_xliff_merge(self):
        """Test merging 2 files modified from a common base"""
        self.test = "Merge"
        self.expected_results = expectedXliffMergeResults
        self.merge(self.fileBase.replace(".po", ".xlf"), self.fileA.replace(".po", ".xlf"), self.fileB.replace(".po", ".xlf"), self.fileMerge.replace(".po", ".xlf"))
        self.expected_results = None
                    

    def set_total_units(self, row_count) :
        self.unit_count = row_count
        assert(row_count == len(self.expected_results))


