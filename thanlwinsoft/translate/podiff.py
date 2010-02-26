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
import gettext
import codecs
import io
import translate.storage.factory

GETTEXT_DOMAIN='podiff'
translation = gettext.install(GETTEXT_DOMAIN, unicode=1)

class Side :
    LEFT, RIGHT = (1, 2)
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
    """Class to compare two translation files or merge two branches"""
    copy_notes = True
    show_resolved_merges = True
    def __init__(self) :
        self.dirty = [False, False]

    def find_unit(self, side, unit) :
        return self.stores[side].findid(unit.getid());
        # units = self.stores[side].findunits(unit.source)
#        if unit.source not in self.source_dict :
#            return None
#        context_dict = self.source_dict[unit.getsource()]
#        ctxt = unit.getcontext()
#        if ctxt not in context_dict : return None
#        return context_dict[ctxt][side]

    def index_storage(self) :
        """Index the source strings for all of the input files for faster lookup."""
        self.source_dict = {}
        for i in range(len(self.stores)) :
            if self.stores[i] is None : continue
            for unit in self.stores[i].unit_iter():
                if unit.getsource() in self.source_dict :
                    context = self.source_dict[unit.getsource()]
                else :
                    context = {}
                if unit.getcontext() in context :
                    units = context[unit.getcontext()]
                else :
                    units = [None, None, None, None]
                units[i] = unit
                context[unit.getcontext()] = units
                self.source_dict[unit.getsource()] = context
        
    def open_storage(self, filename) :
        """Opens translation storage from file. First of all it tries to find a storage by the file extension, 
        if that fails, it defaults to trying to parse it as a po file."""
        storage = None
        try :
            storage = translate.storage.factory.getobject(filename)
            if storage is None or storage.isempty():
                self.show_warning(_("Failed to find any entries in file {0}.").format(filename))
        except ValueError :
            # this occurs when the file has the wrong extension
            # e.g. using a temp file when called directly by a VCS
            try :
                sys.stderr.write(_("Failed to identify type of {0} from extension.\n").format(filename))
                filestream = codecs.open(filename, 'r', 'UTF-8')
                # provide it with a dummy name, because the real name doesn't
                # have the correct extension
                filestream.name = translate.storage.factory._getdummyname(filestream)
                storage_class = translate.storage.factory.getclass(filestream)
                sys.stderr.write(_("Using parser {0}.\n").format(str(storage_class)))
                storage = storage_class.parsefile(filename)
                if storage is None or storage.isempty():
                    self.show_warning(_("Failed to find any entries in file {0}.").format(filename))
            except ValueError as e:
                self.show_warning(_("Failed to parse file {0}. ({1})").format(filename, str(e)))
        return storage

    def diff(self, a, b) :
        """Compare translation units in the files a and b."""
        self.clear()
        self.stores = [None]
        self.stores.append(self.open_storage(a))
        self.stores.append(self.open_storage(b))
        if (self.stores[Side.A] is None) : return
        if (self.stores[Side.B] is None) : return
        self.index_storage()
        self.set_diff_titles(a, b)
        row = 0
        alternateTranslations = 0
        aOnly = 0
        bOnly = 0
        unit_count = 0
        # iterate over left hand side
        for i in self.stores[Side.A].unit_iter():
            bUnit = self.find_unit(Side.B, i)
            state = UnitState.MODE_DIFF
            unit_count += 1
            if (unit_count % 100 == 0) :
                sys.stderr.write('.')
            if (bUnit is not None) :
                aPlurals = [ i.gettarget() ]
                bPlurals = [bUnit.gettarget() ]
                if i.hasplural() :
                    aPlurals = i.gettarget().strings;
                if bUnit.hasplural() :
                    bPlurals = bUnit.gettarget().strings;
                for plural in range(max(len(aPlurals), len(bPlurals))):
                    if plural < len(aPlurals) :
                        if plural < len(bPlurals) :
                            if (aPlurals[plural] != bPlurals[plural]): # a and b different
                                self.show_left(row, unit_count, i, [bUnit], False, state, plural)
                                self.show_right(row, unit_count, bUnit, [i], False, state, plural)
                                row+=1
                                alternateTranslations+=1
                        else :
                            self.show_left(row, unit_count, i, None, False, state, plural)
                            row+=1
                            aOnly+=1
                    else :
                            self.show_right(row, unit_count, bUnit, None, False, state, plural)
                            row+=1
                            bOnly+=1
                        
            else : # a only
                aPlurals = [ i.gettarget() ]
                if i.hasplural() :
                    aPlurals = i.gettarget().strings;
                for plural in range(len(aPlurals)) :
                    self.show_left(row, unit_count, i, None, False, state, plural)
                    row+=1
                    aOnly+=1
            

        for i in self.stores[Side.B].unit_iter():
            a = self.find_unit(Side.A, i)
            if a is None : # b only
                unit_count += 1
                bPlurals = [i.gettarget()]
                if i.hasplural() :
                    bPlurals = i.gettarget().strings
                for plural in range(len(bPlurals)) :
                    self.show_right(row, unit_count, i, None, False, state, plural)
                    row+=1
                    bOnly+=1
        msg = _("{0} differences, {1} only in a, {2} only in b").format(alternateTranslations, aOnly, bOnly)
        self.show_status(msg)
        self.set_total_units(row)
        sys.stderr.write('\n')
        print >> sys.stderr, msg
        
    def merge_from(self, from_side, from_row, unit_index, from_unit, plural, to_side=None) :
        if to_side is None:
            if len(self.stores) == 4 :
                to_side = Side.MERGE
                to_unit = self.find_unit(to_side, from_unit)
            else :
                if from_side == Side.RIGHT : to_side = Side.LEFT
                else : to_side = Side.RIGHT
                to_unit = self.find_unit(to_side, from_unit)
        if (to_unit is None) :
            to_unit = type(from_unit)(from_unit.source)
            self.stores[to_side].addunit(to_unit)

        # this might need to be customized for each supported type
        if (self.copy_notes) :
            # to_unit.removenotes()
            for origin in ("translator", 'developer') : # developer, programmer, and source code are synonymns
                new_notes = []
                old_notes = to_unit.getnotes(origin).split('\n')
                notes = from_unit.getnotes(origin).split('\n')
                for note in notes :
                    if note not in old_notes :
                        new_notes.append(note)
                to_unit.addnote('\n'.join(new_notes), origin)

        if (hasattr(from_unit, "msgctxt")) :
            to_unit.msgctxt = from_unit.msgctxt
        if (plural == 0) :
            to_unit.settarget(from_unit.gettarget())
        else :
            new_target = to_unit.gettarget()
            if unit.hasplural():
                while (len(new_target.strings) < plural + 1) :
                    new_target.strings.append(u"")
                new_target.strings[plural] = from_unit.gettarget().strings[plural]
            to_unit.settarget(new_target)
        if (callable(to_unit.markfuzzy)) :
            to_unit.markfuzzy(False)
        for loc in from_unit.getlocations() :
            to_unit.addlocation(loc)
        if (len(self.stores) == 4) :
            self.dirty[to_side] = True
        else :
            self.dirty[to_side] = True
        self.on_dirty()
        if to_side < Side.MERGE :
            state = UnitState.MODE_DIFF
            self.show_side(to_side, from_row, unit_index, to_unit, None, True, state, plural)
        else :
            state = UnitState.MODE_MERGE | UnitState.RESOLVED
            # show it before we remove from the unresolved list
            self.show_side(to_side, from_row, unit_index, to_unit, None, True, state, plural)
            if from_row in self.unresolved :
                self.resolved.append(from_row)
                msg = _("{0} unresolved").format(len(self.unresolved) - len(self.resolved))
                self.show_status(msg)
                
    def set_plural(self, target_unit, source_unit, plural) :
        new_target = target_unit.gettarget()
        if (source_unit is None) :
            if len(new_target.strings) > plural :
                new_target.strings[plural] = u""
            return
        if not target_unit.hasplural() :
            target_unit.setsource(source_unit.getsource())
        while (len(new_target.strings) <= plural) :
            new_target.strings.append(u"")
        new_target.strings[plural] = source_unit.gettarget().strings[plural]
        target_unit.settarget(new_target)

    def merge(self, base, a, b, merge) :
        self.clear()
        self.stores = []
        self.unresolved = []
        self.resolved = []
        self.stores.append(self.open_storage(base))
        self.stores.append(self.open_storage(a))
        self.stores.append(self.open_storage(b))
        for s in self.stores :
            if (s is None) : return
        self.index_storage()
        mergeStore = object.__new__(self.stores[0].__class__, merge, "UTF-8")
        mergeStore.__init__(merge, "UTF-8")
        mergeStore.filename = merge
        new_headers = self.stores[Side.BASE].parseheader()
        new_headers['add'] = True
        mergeStore.updateheader(**new_headers)
        self.stores.append(mergeStore)
        #print str(self.stores[Side.MERGE])
        self.set_merge_titles(base, a, b, merge)
        overwrite = True
        comments = True
        resolved_from_a = 0
        resolved_from_b = 0
        new_in_a = 0
        new_in_b = 0
        removed = 0
        row = 0
        unit_count = 0
        for base_unit in self.stores[Side.BASE].unit_iter():
            a_unit = self.find_unit(Side.A, base_unit)
            b_unit = self.find_unit(Side.B, base_unit)
            unit_count += 1
            if (unit_count % 100 == 0) :
                sys.stderr.write('.')
            if (a_unit is None) : 
                if (b_unit is None) :
                    # deleted in both, so don't merge into result
                    state = UnitState.RESOLVED | UnitState.MODE_MERGE
                    for plural in range(len(base_unit.gettarget().strings)) :
                        self.show_side(Side.BASE, row, unit_count, base_unit, None, False, state, plural)
                    removed += 1
                    row +=1
                    pass
                else :
                    for plural in range(len(base_unit.gettarget().strings)) :
                        if (len(b_unit.gettarget().strings) > plural) :
                            if (str(base_unit.gettarget().strings[plural]) == str(b_unit.gettarget().strings[plural])) :
                                # removed in A, unchanged in B
                                state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_A
                                removed += 1
                            else :
                                # removed in A, modified in B
                                state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                                self.unresolved.append(row)
                                removed += 1
                            self.show_side(Side.BASE, row, unit_count, base_unit, [b_unit], False, state, plural)
                            self.show_side(Side.B, row, unit_count, b_unit, [base_unit], False, state, plural)
                            row+=1
                        else :
                            # plural doesn't exist in B
                            state = UnitState.RESOLVED | UnitState.MODE_MERGE
                            self.show_side(Side.BASE, row, unit_count, base_unit, None, False, state, plural)
                            row+=1
                    for plural in range(len(base_unit.gettarget().strings), len(b_unit.gettarget().strings)) :
                        # plural only in B
                        state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                        removed += 1
                        self.unresolved.append(row)
                        self.show_side(Side.B, row, unit_count, b_unit, None, False, state, plural)
                        row+=1
            else :
                if (b_unit is None) :
                    for plural in range(len(base_unit.gettarget().strings)) :
                        if (len(a_unit.gettarget().strings) > plural) :
                            if (str(base_unit.gettarget().strings[plural]) == str(a_unit.gettarget().strings[plural])) :
                                # removed in B, unchanged in A
                                state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_B
                                removed += 1
                            else :
                                # removed in B, modified in A
                                state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                                self.unresolved.append(row)
                                removed += 1
                            self.show_side(Side.BASE, row, unit_count, base_unit, [a_unit], False, state, plural)
                            self.show_side(Side.A, row, unit_count, a_unit, [base_unit], False, state, plural)
                            row+=1
                        else :
                            # plural doesn't exist in A
                            state = UnitState.RESOLVED | UnitState.MODE_MERGE
                            self.show_side(Side.BASE, row, unit_count, base_unit, None, False, state, plural)
                            row+=1
                    for plural in range(len(base_unit.gettarget().strings), len(a_unit.gettarget().strings)) :
                        # plural only in A
                        state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                        removed += 1
                        self.unresolved.append(row)
                        self.show_side(Side.A, row, unit_count, a_unit, None, False, state, plural)
                        row+=1
                else : # normal case both a and b present
                    merge_unit = self.stores[Side.MERGE].addsourceunit(base_unit.source)
                    if (base_unit.getcontext() is not None) :
                        merge_unit.msgctxt = base_unit.msgctxt
                    for plural in range(len(base_unit.gettarget().strings)) :
                        if (len(a_unit.gettarget().strings) <= plural) :
                            if (len(b_unit.gettarget().strings) <= plural) : 
                                # neither a nor b has plural
                                set_plural(merge_unit, None, plural)
                                state = UnitState.RESOLVED | UnitState.MODE_MERGE
                                removed += 1
                                self.show_side(Side.BASE, row, unit_count, base_unit, None, False, state, plural)
                                row+=1
                            else :
                                # b has plural, not a
                                state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE | UnitState.USED_B
                                self.unresolved.append(row)
                                self.set_plural(merge_unit, b_unit, plural)
                                self.show_side(Side.BASE, row, unit_count, base_unit, [b_unit], False, state, plural)
                                self.show_side(Side.B, row, unit_count, b_unit, [base_unit], False, state, plural)
                                new_in_b += 1
                                row+=1
                        else :
                            if (len(b_unit.gettarget().strings) <= plural) : 
                                # a has plural, not b
                                state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE | UnitState.USED_A
                                self.unresolved.append(row)
                                self.set_plural(merge_unit, a_unit, plural)
                                self.show_side(Side.BASE, row, unit_count, base_unit, [a_unit], False, state, plural)
                                self.show_side(Side.A, row, unit_count, a_unit, [base_unit], False, state, plural)
                                new_in_a += 1
                                row+=1
                            else :
                                # both have plural
                                if (str(base_unit.gettarget().strings[plural]) == str(a_unit.gettarget().strings[plural])) :
                                # a unchanged
                                    if (str(base_unit.gettarget().strings[plural]) == str(b_unit.gettarget().strings[plural])) :
                                        # unchanged in both, so silently merge
                                        if (plural == 0) : merge_unit.merge(base_unit, overwrite, comments)
                                        else : set_plural(merge_unit, base_unit, plural)
                                    else :
                                        # only b was modified, so use b's text
                                        state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_B
                                        resolved_from_b += 1
                                        if (plural == 0) : merge_unit.merge(b_unit, overwrite, comments)
                                        else : self.set_plural(merge_unit, b_unit, plural)
                                        self.show_side(Side.BASE, row, unit_count, base_unit, [b_unit], False, state, plural)
                                        self.show_side(Side.A, row, unit_count, a_unit, [b_unit], False, state, plural)
                                        self.show_side(Side.B, row, unit_count, b_unit, [base_unit], False, state, plural)
                                        self.show_side(Side.MERGE, row, unit_count, merge_unit, [base_unit], False, state, plural)
                                        row+=1
                                else :
                                    # a modified
                                    if (str(base_unit.gettarget().strings[plural]) == str(b_unit.gettarget().strings[plural]) or
                                        str(a_unit.gettarget().strings[plural]) == str(b_unit.gettarget().strings[plural])) :
                                        # b unchanged or the same as a, so use a
                                        state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_A
                                        resolved_from_a += 1
                                        if (plural == 0) : merge_unit.merge(a_unit, overwrite, comments)
                                        else : self.set_plural(merge_unit, a_unit, plural)
                                        self.show_side(Side.BASE, row, unit_count, base_unit, [a_unit], False, state, plural)
                                        self.show_side(Side.A, row, unit_count, a_unit, [base_unit], False, state, plural)
                                        self.show_side(Side.B, row, unit_count, b_unit, [base_unit, a_unit], False, state, plural)
                                        self.show_side(Side.MERGE, row, unit_count, merge_unit, [base_unit], False, state, plural)
                                        row+=1
                                    else :
                                        # both a and b changed
                                        state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                                        self.unresolved.append(row)
                                        if (plural == 0) : merge_unit.merge(base_unit, overwrite, comments)
                                        else : self.set_plural(merge_unit, base_unit, plural)
                                        self.show_side(Side.BASE, row, unit_count, base_unit, [a_unit, b_unit], False, state, plural)
                                        self.show_side(Side.A, row, unit_count, a_unit, [base_unit, b_unit], False, state, plural)
                                        self.show_side(Side.B, row, unit_count, b_unit, [base_unit, a_unit], False, state, plural)
                                        self.show_side(Side.MERGE, row, unit_count, merge_unit, [a_unit, b_unit], False, state, plural)
                                        row+=1
                    for plural in range(len(base_unit.gettarget().strings), len(a_unit.gettarget().strings)) :
                        # plural in a, not in base
                        if (len(b_unit.gettarget().strings) <= plural) :
                            # plural not in B
                            state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_A
                            self.set_plural(merge_unit, a_unit, plural)
                            self.show_side(Side.A, row, unit_count, a_unit, None, False, state, plural)
                            self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state, plural)
                            resolved_from_a += 1
                        else :
                            if (str(b_unit.gettarget().strings[plural]) == str(a_unit.gettarget().strings[plural])) :
                                state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_A
                                self.set_plural(merge_unit, a_unit, plural)
                                self.show_side(Side.A, row, unit_count, a_unit, None, False, state, plural)
                                self.show_side(Side.B, row, unit_count, b_unit, None, False, state, plural)
                                self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state, plural)
                                resolved_from_a += 1
                            else :
                                state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                                self.unresolved.append(row)
                                self.set_plural(merge_unit, a_unit, plural)
                                self.show_side(Side.A, row, unit_count, a_unit, [b_unit], False, state, plural)
                                self.show_side(Side.B, row, unit_count, b_unit, [a_unit], False, state, plural)
                                self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state, plural)
                        row+=1
                    for plural in range(len(base_unit.gettarget().strings), len(b_unit.gettarget().strings)) :
                        if plural >= len(a_unit.gettarget().strings) :
                            state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_B
                            self.set_plural(merge_unit, b_unit, plural)
                            self.show_side(Side.B, row, unit_count, a_unit, None, False, state, plural)
                            self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state, plural)
                            resolved_from_b += 1
                            new_in_b += 1
                            row+=1
        # TODO fix the case where a/b has a plural and base didn't since the source strings compare
        # to be different, you can get both listed as separate entries in the table
        plural_warning = _("{0}\nID '{1}' has no plural in base, but has a plural with ID '{2}' in {3}. Only one should be merged.")
        # now find new entries in a
        for a_unit in self.stores[Side.A].unit_iter():
            base_unit = self.find_unit(Side.BASE, a_unit)
            if base_unit is not None : continue
            unit_count += 1
            b_unit = self.find_unit(Side.B, a_unit)
            ambiguous_plural = False
            if (a_unit.hasplural()) :
                main_id = str(a_unit.getsource())
                non_plurals = self.stores[Side.BASE].findunits(main_id)
                for non_plural in non_plurals :
                    if non_plural.getcontext() == a_unit.getcontext() :
                        ambiguous_plural = True
                        if (b_unit is None) :
                            self.show_warning(plural_warning.format(a_unit.getcontext(), main_id, a_unit.getsource().strings[1], _("File A")))
                        else :
                            self.show_warning(plural_warning.format(a_unit.getcontext(), main_id, a_unit.getsource().strings[1], _("Files A and B")))
                        break
                    
            merge_unit = self.stores[Side.MERGE].addsourceunit(a_unit.source)
            if (a_unit.getcontext() is not None) :
                merge_unit.msgctxt = a_unit.msgctxt
            for plural in range(len(a_unit.gettarget().strings)) :
                if (b_unit is None or (len(a_unit.gettarget().strings) > plural and
                    str(b_unit.gettarget().strings[plural]) == str(a_unit.gettarget().strings[plural]))):
                    # use a
                    state = UnitState.MODE_MERGE | UnitState.USED_A
                    if ambiguous_plural : state |= UnitState.AMBIGUOUS
                    else : state |= UnitState.RESOLVED
                    if (plural == 0) :
                        merge_unit.merge(a_unit, overwrite, comments)
                    else :
                        self.set_plural(merge_unit, a_unit, plural)
                    self.show_side(Side.A, row, unit_count, a_unit, None, False, state, plural)
                    resolved_from_a += 1
                    new_in_a += 1
                    if (b_unit is not None) :
                        self.show_side(Side.B, row, unit_count, b_unit, None, False, state, plural)
                        new_in_b += 1
                    self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state, plural)
                    row+=1
                else :
                    # new entry is also in b
                    state = UnitState.AMBIGUOUS | UnitState.MODE_MERGE
                    new_in_a += 1
                    new_in_b += 1
                    self.unresolved.append(row)
                    # don't know what to merge yet
                    self.show_side(Side.A, row, unit_count, a_unit, [b_unit], False, state, plural)
                    self.show_side(Side.B, row, unit_count, b_unit, [a_unit], False, state, plural)
                    self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state, plural)
                    row+=1
            if (b_unit is not None) :
                for plural in range(len(a_unit.gettarget().strings), len(b_unit.gettarget().strings)) :
                    state = UnitState.MODE_MERGE | UnitState.USED_B
                    if ambiguous_plural : state |= UnitState.AMBIGUOUS
                    else : state |= UnitState.RESOLVED
                    resolved_from_b += 1
                    new_in_b += 1
                    self.set_plural(merge_unit, b_unit, plural)
                    self.show_side(Side.B, row, unit_count, b_unit, None, False, state)
                    self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state)
                    row+=1
        # find new entries only in b
        for b_unit in self.stores[Side.B].unit_iter():
            base_unit = self.find_unit(Side.BASE, b_unit)
            if base_unit is not None : continue
            a_unit = self.find_unit(Side.A, b_unit)
            if (a_unit is None):
                # use b
                unit_count += 1
                state = UnitState.RESOLVED | UnitState.MODE_MERGE | UnitState.USED_B
                resolved_from_b += 1
                new_in_b += 1
                merge_unit = self.stores[Side.MERGE].addsourceunit(b_unit.source)
                if (b_unit.getcontext() is not None) :
                    merge_unit.msgctxt = b_unit.msgctxt
                merge_unit.merge(b_unit, overwrite, comments)
                if (b_unit.hasplural()) :
                    main_id = str(b_unit.getsource())
                    non_plurals = self.stores[Side.BASE].findunits(main_id)
                    for non_plural in non_plurals :
                        if non_plural.getcontext() == b_unit.getcontext() :
                            state ^= UnitState.RESOLVED
                            state |= UnitState.AMBIGUOUS
                            self.show_warning(plural_warning.format(b_unit.getcontext(), main_id, b_unit.getsource().strings[1], _("File B")))
                            break
                for plural in range(len(b_unit.gettarget().strings)) :
                    if (plural > 0) : self.set_plural(merge_unit, b_unit, plural)
                    self.show_side(Side.B, row, unit_count, b_unit, None, False, state, plural)
                    self.show_side(Side.MERGE, row, unit_count, merge_unit, None, False, state, plural)
                    row+=1
        self.dirty[Side.MERGE] = True
        self.on_dirty()
        msg = _("{0} unresolved; {1} resolved from A; {2} resolved from B; {3} new in A; {4} new in B; {5} removed").format(len(self.unresolved), resolved_from_a, resolved_from_b, new_in_a, new_in_b, removed)
        self.show_status(msg)
        self.set_total_units(row)
        sys.stderr.write('\n')

       