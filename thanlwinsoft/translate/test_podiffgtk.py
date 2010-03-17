#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Keith Stribley http://www.thanlwinsoft.org/ 
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

import pygtk
pygtk.require('2.0')
import gtk
import translate.storage.factory

from thanlwinsoft.translate.podiff import Side
from thanlwinsoft.translate.podiffgtk import PoDiffGtk
from thanlwinsoft.translate.podiffgtk import PoUnitGtk

class TestPoDiffGtk(object):
    def __init__(self):
        self.podiffgtk = PoDiffGtk()
    
    def test_diff(self):
        self.podiffgtk.diff("testA.po", "testB.po")
        assert(self.podiffgtk.get_unit_count() > 0)
        
    def test_unit_display(self):
        self.podiffgtk.show_units(self.podiffgtk.get_unit_count() - 1)
        self.podiffgtk.show_units(0)
        testid = "test2 modify in A"
        aunit = self.podiffgtk.stores[Side.LEFT].findid(testid)
        bunit = self.podiffgtk.stores[Side.RIGHT].findid(testid)
        orig_a = aunit.gettarget()
        orig_b = bunit.gettarget()
        assert(aunit.gettarget() != bunit.gettarget())
        test_frame = self.podiffgtk.unit_frames[(Side.LEFT, 0)]
        assert(test_frame.plural == 0)
        assert(test_frame.source_buffer.get_text(test_frame.source_buffer.get_start_iter(), 
                                                 test_frame.source_buffer.get_end_iter())
                                                 == unicode(aunit.getsource()))
        assert(test_frame.target_buffer.get_text(test_frame.target_buffer.get_start_iter(), 
                                                 test_frame.target_buffer.get_end_iter())
                                                 == unicode(aunit.gettarget()))
        test_frame.copy_button.released()
        assert(self.podiffgtk.dirty[Side.RIGHT])
        assert(orig_a == bunit.gettarget())
        testid = "test3 modify in B"
        aunit = self.podiffgtk.stores[Side.LEFT].findid(testid)
        bunit = self.podiffgtk.stores[Side.RIGHT].findid(testid)
        orig_a = aunit.gettarget()
        orig_b = bunit.gettarget()
        assert(aunit.gettarget() != bunit.gettarget())
        test_frame = self.podiffgtk.unit_frames[(Side.RIGHT, 1)]
        assert(test_frame.source_buffer.get_text(test_frame.source_buffer.get_start_iter(), 
                                                 test_frame.source_buffer.get_end_iter())
                                                 == unicode(bunit.getsource()))
        assert(test_frame.target_buffer.get_text(test_frame.target_buffer.get_start_iter(), 
                                                 test_frame.target_buffer.get_end_iter())
                                                 == unicode(bunit.gettarget()))
        test_frame.copy_button.released()
        assert(self.podiffgtk.dirty[Side.LEFT])
        assert(aunit.gettarget() == orig_b)

        testid = "modify in both\04test19 with context"
        self.podiffgtk.show_units(13)
        test_frame = self.podiffgtk.unit_frames[(Side.LEFT, 0)]
        aunit = self.podiffgtk.stores[Side.LEFT].findid(testid)
        bunit = self.podiffgtk.stores[Side.RIGHT].findid(testid)
        assert(test_frame.context_buffer.get_text(test_frame.context_buffer.get_start_iter(), 
                                                 test_frame.context_buffer.get_end_iter())
                                                 == unicode(aunit.getcontext()))
        assert(test_frame.source_buffer.get_text(test_frame.source_buffer.get_start_iter(), 
                                                 test_frame.source_buffer.get_end_iter())
                                                 == unicode(aunit.getsource()))
        assert(test_frame.target_buffer.get_text(test_frame.target_buffer.get_start_iter(), 
                                                 test_frame.target_buffer.get_end_iter())
                                                 == unicode(aunit.gettarget()))
        
        # now check a plural
        test_frame = self.podiffgtk.unit_frames[(Side.LEFT, 2)]
        testid = "test20 single"
        aunit = self.podiffgtk.stores[Side.LEFT].findid(testid)
        bunit = self.podiffgtk.stores[Side.RIGHT].findid(testid)
        assert(test_frame.plural == 1)
        assert(test_frame.source_buffer.get_text(test_frame.source_buffer.get_start_iter(), 
                                                 test_frame.source_buffer.get_end_iter())
                                                 == unicode(aunit.getsource().strings[1]))
        assert(test_frame.target_buffer.get_text(test_frame.target_buffer.get_start_iter(), 
                                                 test_frame.target_buffer.get_end_iter())
                                                 == unicode(aunit.gettarget().strings[1]))

    def test_merge(self):
        self.podiffgtk.merge("testBase.po", "testA.po", "testB.po", "testMerge.po")
        assert(self.podiffgtk.get_unit_count() > 0)
        assert(self.podiffgtk.dirty[Side.MERGE])
        
    def test_scroll(self):
        self.podiffgtk.show_units(self.podiffgtk.get_unit_count() - 1)
        self.podiffgtk.show_units(0)

    def test_filter(self):
        self.podiffgtk.builder.get_object("toolbuttonFilterResolved").set_active(True)
        test_frame = self.podiffgtk.unit_frames[(Side.LEFT, 0)]
        assert(test_frame.unit.getsource() == "test4 modify in A & B")
        unresolved_count = len(self.podiffgtk.unresolved)
        assert(len(self.podiffgtk.resolved) == 0)
        test_frame.copy_button.released()
        assert(len(self.podiffgtk.resolved) == 1)
        # This should be the first unresolved entry
        self.podiffgtk.builder.get_object("toolbuttonFilterResolved").set_active(False)
        test_frame = self.podiffgtk.unit_frames[(Side.BASE, 0)]
        assert(test_frame.unit.getsource() == "test2 modify in A")
        # the unresolved count is only updated when the filter is set back on
        self.podiffgtk.builder.get_object("toolbuttonFilterResolved").set_active(True)
        assert(len(self.podiffgtk.unresolved) == unresolved_count - 1)

    def test_search(self):
        # check a failing search doesn't loop
        assert(False == self.podiffgtk.do_search(u"Does not exist", True, True, True, False, False, None))
        # should be found in case-insensitive
        assert(True == self.podiffgtk.do_search(u"a and b", True, True, True, False, False, None))
        # lower case should not be found when case-sensitive
        assert(False == self.podiffgtk.do_search(u"a and b", True, True, True, True, False, None))
        assert(True == self.podiffgtk.do_search(u"A and B", False, True, False, True, False, None))
        self.check_selection(u"A and B")
        # check context search
        assert(True == self.podiffgtk.do_search(u"modify in both", True, True, True, False, False, None))
        assert(True == self.podiffgtk.do_search(u"modify in both", True, False, False, False, False, None))
        self.check_selection(u"modify in both")
        # should not be found if context is excluded
        assert(False == self.podiffgtk.do_search(u"modify in both", False, True, True, False, False, None))
        # test search in translation
        assert(True == self.podiffgtk.do_search(u"Aမှာ", False, False, True, False, False, None))
        pos = self.check_selection(u"Aမှာ")
        assert(True == self.podiffgtk.do_search(u"Aမှာ", False, False, True, False, False, None))
        next_pos = self.check_selection(u"Aမှာ")
        assert(next_pos.row > pos.row or (next_pos.row == pos.row and next_pos.side > pos.side))
        # go backwards
        assert(True == self.podiffgtk.do_search(u"Aမှာ", False, False, True, False, True, None))
        prev_pos = self.check_selection(u"Aမှာ")
        assert(prev_pos.row < next_pos.row or (next_pos.row == next_pos.row and prev_pos.side < next_pos.side))
        assert(prev_pos == pos)
        
    def test_replace(self):
        new_text = u"[က]မှာ"
        old_text = u"Aမှာ"
        self.podiffgtk.do_search(old_text, False, False, True, False, False, None)
        pos = self.check_selection(old_text)
        while (pos.side != Side.MERGE) :
            self.podiffgtk.do_search(old_text, False, False, True, False, False, None)
            pos = self.check_selection(old_text)
        unit_data = self.podiffgtk.unit_dict[pos]
        old_index = unit_data.unit.gettarget().strings[unit_data.plural].find(old_text)
        old_len = len(unit_data.unit.gettarget().strings[unit_data.plural])
        self.podiffgtk.do_replace(old_text, new_text, False, None)
        pos = self.check_selection(new_text)
        new_len = len(unit_data.unit.gettarget().strings[unit_data.plural])
        assert(unit_data.unit.gettarget().strings[unit_data.plural].find(new_text) == old_index)
        assert(new_len == old_len - len(old_text) + len(new_text))

    def check_selection(self, text):
        focus = self.podiffgtk.win.get_focus()
        assert isinstance(focus, gtk.TextView)
        b = focus.get_buffer()
#        assert(b.get_has_selection())
        selection = b.get_selection_bounds()
        assert(b.get_text(selection[0], selection[1]) == text)
        return PoUnitGtk.find_frame_pos(focus)

    def test_save(self):
        """Test that saving the results works"""
        assert(self.podiffgtk.dirty == [False, False, False, True])
        self.podiffgtk.saveAll()
        # read back and check
        storage = translate.storage.factory.getobject("testMerge.po")
        for i in self.podiffgtk.stores[Side.MERGE].unit_iter():
            saved_unit = storage.findid(i.getid())
            assert(i.getcontext() == saved_unit.getcontext())
            assert(i.getsource() == saved_unit.getsource())
            assert(i.gettarget() == saved_unit.gettarget())
