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
import types
import translate.storage.factory
import translate.storage.pypo

class Side :
    LEFT, RIGHT = (0, 1)
    BASE, A, B, MERGE = (0, 1, 2, 3)
    
class UnitState :
    """Bits fields to handle state of a translation unit"""
    RESOLVED = 0x1
    AMBIGUOUS = 0x2
    USED_A = 0x4
    USED_B = 0x8
    MODE_DIFF = 0x100
    MODE_MERGE = 0x200
    

class PODiff(object) :
    copy_notes = True
    show_resolved_merges = True
    def __init__(self) :
        self.dirty = [False, False]

    def diff(self, a, b) :
        self.clear()
        self.stores = []
        self.stores.append(translate.storage.factory.getobject(a))
        self.stores.append(translate.storage.factory.getobject(b))
        self.set_diff_titles(a, b)
        row = 0
        alternateTranslations = 0
        aOnly = 0
        bOnly = 0
        # iterate over left hand side
        for i in self.stores[0].unit_iter():
            bUnit = self.stores[1].findunit(i.source)
            if (bUnit is not None) :
                if (i.gettarget() != bUnit.gettarget()): # a and b different
                    self.show_left(row, i, bUnit, False)
                    self.show_right(row, bUnit, i, False)
                    row+=1
                    alternateTranslations+=1
            else : # a only
                self.show_left(row, i)
                row+=1
                aOnly+=1

        for i in self.stores[1].unit_iter():
            a = self.stores[0].findunit(i.source)
            if a is None : # b only
                self.show_right(row, i)
                row+=1
                bOnly+=1
        msg = "{0} differences, {1} only in a, {2} only in b".format(alternateTranslations, aOnly, bOnly)
        self.show_status(msg)
        print >> sys.stderr, "" + str(alternateTranslations) + " differences"
        print >> sys.stderr, "" + str(aOnly) + " only in a"
        print >> sys.stderr, "" + str(bOnly) + " only in b"
        
    def merge_from(self, from_side, from_row, from_unit, to_side=None) :
        if to_side is None:
            if len(self.stores) == 4 :
                to_side = Side.MERGE
            else :
                if from_side == Side.RIGHT : to_side = Side.LEFT
                else : to_side = Side.RIGHT
        to_unit = self.stores[to_side].findunit(from_unit.source)
        if (to_unit is None) :
            if (isinstance(tounit, translate.storage.pypo.pounit)):
                to_unit = translate.storage.pypo.pounit(from_unit.source)
            else :
                if (isinstance (to_unit, translate.storage.pypo.xliffunit)) :
                    to_unit = translate.storage.pypo.xliffunit(from_unit.source)
                else : raise Exception("Unsupported unit type:" + to_unit.__class__)
            self.stores[to_side].addunit(to_unit)

        # this might need to be customized for each supported type
        if (self.copy_notes) :
            to_unit.removenotes()
            for origin in ("translator", 'developer', 'programmer', 'source code') :
                new_notes = []
                notes = from_unit.getnotes(origin).split('\n')
                for note in notes :
                    new_notes.append(note)
                to_unit.addnote('\n'.join(new_notes), origin)

        if (hasattr(from_unit, "msgctxt")) :
            to_unit.msgctxt = from_unit.msgctxt
        to_unit.settarget(from_unit.gettarget())
        for loc in from_unit.getlocations() :
            to_unit.addlocation(loc)
        self.dirty[to_side] = True
        self.show_side(to_side, from_row, to_unit, None, True)

    def merge(self, base, a, b, merge) :
        self.clear()
        self.stores = []
        self.unresolved = []
        self.stores.append(translate.storage.factory.getobject(base))
        self.stores.append(translate.storage.factory.getobject(a))
        self.stores.append(translate.storage.factory.getobject(b))
        mergeStore = object.__new__(self.stores[0].__class__, merge, "UTF-8")
        mergeStore.__init__(merge, "UTF-8")
        mergeStore.filename = merge
        self.stores.append(mergeStore)
        print str(self.stores[Side.MERGE])
        self.set_merge_titles(base, a, b, merge)
        overwrite = True
        comments = True
        row = 0
        for base_unit in self.stores[Side.BASE].unit_iter():
            a_unit = self.stores[Side.A].findunit(base_unit.source)
            b_unit = self.stores[Side.B].findunit(base_unit.source)
            if (a_unit is None) : 
                if (b_unit is None) :
                    # deleted in both, so don't merge into result
                    pass
                else :
                    if (base_unit.gettarget() == b_unit.gettarget()) :
                        state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_A
                    else :
                        state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                        self.unresolved.append(row)
                    self.show_side(Side.BASE, row, base_unit, None, False, state)
                    self.show_side(Side.B, row, b_unit, base_unit, False, state)
                    row+=1
            else :
                if (b_unit is None) :
                    if (base_unit.gettarget() == a_unit.gettarget()) :
                        state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_B
                    else :
                        state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                        self.unresolved.append(row)
                    self.show_side(Side.BASE, row, base_unit, None, False, state)
                    self.show_side(Side.A, row, a_unit, base_unit, False, state)
                    row+=1
                else : # normal case both a and b present
                    if (base_unit.gettarget() == a_unit.gettarget()) :
                        # a unchanged
                        if (base_unit.gettarget() == b_unit.gettarget()) :
                            # unchanged in both, so silently merge
                            merge_unit = self.stores[Side.MERGE].addsourceunit(base_unit.source)
                            merge_unit.merge(base_unit, overwrite, comments)
                        else :
                            # only b was modified, so use b's text
                            state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_B
                            merge_unit = self.stores[Side.MERGE].addsourceunit(base_unit.source)
                            merge_unit.merge(b_unit, overwrite, comments)
                            self.show_side(Side.BASE, row, base_unit, None, False, state)
                            self.show_side(Side.A, row, a_unit, base_unit, False, state)
                            self.show_side(Side.B, row, b_unit, base_unit, False, state)
                            self.show_side(Side.MERGE, row, merge_unit, base_unit, False, state)
                            row+=1
                    else :
                        # a modified
                        if (base_unit.gettarget() == b_unit.gettarget() or
                            a_unit.gettarget() == b_unit.gettarget()) :
                            # b unchanged or the same as a, so use a
                            state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_A
                            merge_unit = self.stores[Side.MERGE].addsourceunit(base_unit.source)
                            merge_unit.merge(a_unit, overwrite, comments)
                            self.show_side(Side.BASE, row, base_unit, None, False, state)
                            self.show_side(Side.A, row, a_unit, base_unit, False, state)
                            self.show_side(Side.B, row, b_unit, base_unit, False, state)
                            self.show_side(Side.MERGE, row, merge_unit, base_unit, False, state)
                            row+=1
                        else :
                            # both a and b changed
                            state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                            self.unresolved.append(row)
                            merge_unit = self.stores[Side.MERGE].addsourceunit(base_unit.source)
                            merge_unit.merge(base_unit, overwrite, comments)
                            self.show_side(Side.BASE, row, base_unit, None, False, state)
                            self.show_side(Side.A, row, a_unit, base_unit, False, state)
                            self.show_side(Side.B, row, b_unit, base_unit, False, state)
                            self.show_side(Side.MERGE, row, merge_unit, base_unit, False, state)
                            row+=1
        # now find new entries in a
        for a_unit in self.stores[Side.A].unit_iter():
            base_unit = self.stores[Side.BASE].findunit(a_unit.source)
            if base_unit is not None : continue
            b_unit = self.stores[Side.B].findunit(a_unit.source)
            if (b_unit is None or b_unit.gettarget() == a_unit.gettarget()):
                # use a
                state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_A
                merge_unit = self.stores[Side.MERGE].addsourceunit(a_unit.source)
                merge_unit.merge(a_unit, overwrite, comments)
                self.show_side(Side.A, row, a_unit, None, False, state)
                if (b_unit is not None) :
                    self.show_side(Side.B, row, b_unit, None, False, state)
                self.show_side(Side.MERGE, row, merge_unit, None, False, state)
                row+=1
            else :
                # new entry is also in b
                state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                self.unresolved.append(row)
                merge_unit = self.stores[Side.MERGE].addsourceunit(a_unit.source)
                # don't know what to merge yet
                self.show_side(Side.A, row, a_unit, b_unit, False, state)
                self.show_side(Side.B, row, b_unit, a_unit, False, state)
                self.show_side(Side.MERGE, row, merge_unit, base_unit, False, state)
                row+=1
        # find new entries only in b
        for b_unit in self.stores[Side.B].unit_iter():
            base_unit = self.stores[Side.BASE].findunit(b_unit.source)
            if base_unit is not None : continue
            a_unit = self.stores[Side.A].findunit(b_unit.source)
            if (a_unit is None):
                # use b
                state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_B
                merge_unit = self.stores[Side.MERGE].addsourceunit(b_unit.source)
                merge_unit.merge(b_unit, overwrite, comments)
                self.show_side(Side.B, row, b_unit, None, False, state)
                self.show_side(Side.MERGE, row, merge_unit, None, False, state)
                row+=1
        self.dirty[Side.MERGE] = True
        self.on_dirty()

        
