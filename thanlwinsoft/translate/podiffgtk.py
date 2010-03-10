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

import pygtk
pygtk.require('2.0')
import gtk
import pango
import sys
import os.path
import gettext
import ConfigParser
from translate.misc.multistring import multistring
import translate.storage.factory

from thanlwinsoft.translate.podiff import PoDiff, Side, UnitState
from textdiff import find_matches

GETTEXT_DOMAIN='podiff'
translation = gettext.install(GETTEXT_DOMAIN, unicode=1)


class PoUnitData(object) :
    CONTEXT, SOURCE, TARGET = (0, 1, 2)
    def __init__(self, index, unit, cf_units, state, plural) :
        self.index = index
        self.unit = unit
        self.cf_units = cf_units
        self.state = state
        self.plural = plural

    def find(self, text, use_context, use_msgid, use_translation, case_sensitive, backwards) :
        """Search for the specified text in the current unit and return the component that matched at the offset"""
        data = []
        if (self.unit.hasplural()) :
            if (use_context) : data.append((PoUnitData.CONTEXT, self.unit.getcontext()))
            if (use_msgid) : data.append((PoUnitData.SOURCE, self.unit.getsource().strings[self.plural]))
            if (use_translation) : data.append((PoUnitData.TARGET, self.unit.gettarget().strings[self.plural]))
        else :
            if (use_context) : data.append((PoUnitData.CONTEXT, self.unit.getcontext()))
            if (use_msgid) : data.append((PoUnitData.SOURCE, self.unit.getsource()))
            if (use_translation) : data.append((PoUnitData.TARGET, self.unit.gettarget()))
        if (backwards) : data.reverse()
        
        for component, hay in data :
            if not case_sensitive : hay = hay.lower()
            if (backwards) :
                found_at = hay.rfind(text)
            else :
                found_at = hay.find(text)
            if found_at != -1 :
                # found the text
                return (component, found_at)
        return None

class PoUnitGtk(object) :
    """Displays a frame showing the contents of a translatable unit."""
    po_diff = None
    diff_colors = [gtk.gdk.Color(1.0,0.5,0.5), gtk.gdk.Color(0.5,1.0,0.5), gtk.gdk.Color(0.5,0.5,1.0), gtk.gdk.Color(1.0,1.0,0.5), gtk.gdk.Color(1.0,0.5,1.0), gtk.gdk.Color(0.5,1.0,1.0), gtk.gdk.Color(0.5,0.5,0.5)]
    def __init__(self, side, state):
        self.side = side
        self.unit_index = None
        self.unit_change = False
        self.scrolled = gtk.ScrolledWindow()
        self.scrolled.set_property("hscrollbar-policy", gtk.POLICY_AUTOMATIC)
        self.scrolled.set_property("vscrollbar-policy", gtk.POLICY_AUTOMATIC)
        self.viewport = gtk.Viewport()
        self.frame = gtk.Frame()
        self.frame.connect("scroll-event", self.po_diff.unitVscrollbar_scroll_event_cb)
        self.vbox = gtk.VBox(False, 2)
        self.title_box = gtk.HBox()
        self.copy_button = gtk.Button()
        self.copy_button.connect("released", self.copy_button_release_event_cb)
        self.source = gtk.TextView()
        self.source.set_wrap_mode(gtk.WRAP_WORD)
        self.source_buffer = gtk.TextBuffer()
        self.source_buffer.set_text(_("Source"))
        self.source.set_buffer(self.source_buffer)
        self.source.set_editable(False)
        self.source.show()
        self.target = gtk.TextView()
        self.target_buffer = gtk.TextBuffer()
        self.diff_tag = []
        for i in range(3) :
            self.diff_tag.append(gtk.TextTag(name="diff" + str(i)))
            self.diff_tag[i].set_property("background-gdk", self.diff_colors[self.side + i])
            self.target_buffer.get_tag_table().add(self.diff_tag[i])
        self.edit_tag = gtk.TextTag(name="edit")
        self.edit_tag.set_property("background-gdk", self.diff_colors[len(self.diff_colors) - 1])
        self.target_buffer.get_tag_table().add(self.edit_tag)
        self.target_buffer.set_text("Target")
        self.target.set_buffer(self.target_buffer)
        self.target.set_editable(True)
        self.target.show()
        self.context = gtk.TextView()
        self.context_buffer = gtk.TextBuffer()
        self.context_buffer.set_text(_("Context"))
        self.context.set_tooltip_text(_("Context"))
        self.context.set_buffer(self.context_buffer)
        self.context.set_editable(False)
        self.context.show()
        self.copy_button.show()
        self.id_label = gtk.Label()
        self.id_label.show()
        self.img = None
        if (state & UnitState.MODE_MERGE) :
            self.frame.set_size_request(125, -1)
            if (self.side == Side.BASE or self.side == Side.A or self.side == Side.B) :
                self.copy_button.set_label(">>")
                arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_IN)
                arrow.show()
                self.frame.set_label_align(1.0, .5)
                self.title_box.add(self.id_label)
                self.title_box.add(arrow)
                self.title_box.add(self.copy_button)
            else :
                self.img = gtk.Image()
                self.img.show()             
                self.title_box.add(self.img)
                self.title_box.add(self.id_label)
                self.copy_button.hide()
                pass            
        else :
            self.frame.set_size_request(250, -1)
            if (self.side == Side.LEFT): 
                self.copy_button.set_label(">>")
                arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_IN)
                arrow.show()
                self.frame.set_label_align(1.0, .5)
                self.title_box.add(self.id_label)
                self.title_box.add(arrow)
                self.title_box.add(self.copy_button)
            else :
                self.copy_button.set_label("<<")
                arrow = gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_IN)
                arrow.show()
                self.frame.set_label_align(0.0, .5)
                self.title_box.add(self.copy_button)
                self.title_box.add(arrow)
                self.title_box.add(self.id_label)
        self.frame.set_label_widget(self.title_box)
        self.target.set_wrap_mode(gtk.WRAP_WORD)
        self.viewport.add(self.vbox)
        self.vbox.add(self.context)
        self.vbox.add(self.source)
        self.vbox.add(self.target)
        self.vbox.show()
        self.title_box.show()
        self.scrolled.show()
        self.viewport.show()
        self.scrolled.add(self.viewport)
        self.frame.add(self.scrolled)

    def set_unit(self, unit_data, modified=False) :
        self.unit_change = True
        self.plural = unit_data.plural    
        if (self.plural > 0) :
            self.source.set_tooltip_text(_("Source (plural)"))
            self.target.set_tooltip_text(_("Target [{0:d}]").format(self.plural))
        else :
            self.source.set_tooltip_text(_("Source"))
            self.target.set_tooltip_text(_("Target"))
        if (self.side == Side.MERGE) :
            if (unit_data.state & UnitState.RESOLVED) :
                self.img.set_from_file(os.path.dirname(__file__) + "/merged.png")
            else :
                if (unit_data.state & UnitState.AMBIGUOUS):           
                    self.img.set_from_file(os.path.dirname(__file__) + "/unmerged.png")
                else :
                    if self.img is not None and hasattr(self.img, 'clear') :
                        self.img.clear()

#        self.source_buffer.set_text(unit.getid())
#        self.target_buffer.set_text(unit.gettarget())
        self.unit_index = unit_data.index
        self.unit = unit_data.unit
        if (self.unit.hasplural()) :
            self.id_label.set_text(_("{0:d} [{1:d}]").format(self.unit_index, self.plural))
        else :
            self.id_label.set_text(str(self.unit_index))
        comments = str(self.unit.getnotes())
        for l in self.unit.getlocations() :
            comments += "\n" + l
        self.id_label.set_tooltip_text(comments)
        if (self.plural == 0) :
            self.source_buffer.set_text(self.unit.source)
        else :
            self.source_buffer.set_text(self.unit.source.strings[1])
        if self.unit.hasplural() :
            if (len(self.unit.gettarget().strings) > self.plural) :
                self.target_buffer.set_text(self.unit.gettarget().strings[self.plural])
            else :
                self.target_buffer.set_text(u"")
        else :
            if (self.plural == 0) :
                self.target_buffer.set_text(self.unit.gettarget());
            else :
                self.target_buffer.set_text(u"")
        self.context_buffer.set_text(self.unit.getcontext())
        self.target_buffer.connect("insert-text", self.insert_text_event_cb, self.target)
        self.target_buffer.connect("delete-range", self.delete_range_event_cb, self.target)
        self.target_buffer.connect("changed", self.changed_event_cb, self.target)
        if len(self.unit.getcontext()) > 0 :
            self.context.show()
        else :
            self.context.hide()
        self.po_diff.on_dirty()
        if (unit_data.cf_units is not None) :
            # print unit.gettarget()
            # print cf_unit.gettarget()
            plurals = [ self.unit.gettarget() ]
            if self.unit.hasplural():
                plurals = self.unit.gettarget().strings
            for j in range(len(unit_data.cf_units)) :
                cf_unit = unit_data.cf_units[j]
                cf_plurals = [ cf_unit.gettarget() ]
                if cf_unit.hasplural() :
                    cf_plurals = cf_unit.gettarget().strings
                if (len(plurals) <= self.plural or len(cf_plurals) <= self.plural) :
                    continue
                common = find_matches(plurals[self.plural], cf_plurals[self.plural])
                pos = 0
                for i in range(len(common)) :
                    if (pos < common[i][0]) : 
                        s_iter = self.target_buffer.get_iter_at_offset(pos)
                        e_iter = self.target_buffer.get_iter_at_offset(common[i][0])
                        self.target_buffer.apply_tag_by_name("diff" + str(j), s_iter, e_iter)
                    pos = common[i][0] + common[i][2]
                if pos < len(plurals[self.plural]) :
                    s_iter = self.target_buffer.get_iter_at_offset(pos)
                    e_iter = self.target_buffer.get_iter_at_offset(len(plurals[self.plural]))
                    self.target_buffer.apply_tag_by_name("diff" + str(j), s_iter, e_iter)
        if (modified) :
            self.target_buffer.remove_all_tags(self.target_buffer.get_start_iter(), self.target_buffer.get_end_iter())
            if self.side == Side.LEFT :
                self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(0.0, 1.0, 0.0))
            else :
                self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(1.0, 0.0, 0.0))
        else :
            self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))
        self.unit_change = False

    @staticmethod
    def find_frame_pos(widget) :
        if widget is None : return None
        frame = widget.get_parent()
        while (not isinstance(frame, gtk.Frame)) :
            frame = frame.get_parent()
            if frame is None : return None
        side = frame.get_parent().child_get_property(frame, "left-attach")

        row = frame.get_parent().child_get_property(frame, "top-attach")
        filter_resolved = PoUnitGtk.po_diff.builder.get_object("toolbuttonFilterResolved").get_active()
        if filter_resolved :
            row = PoUnitGtk.po_diff.unresolved[row + PoUnitGtk.po_diff.prev_page - 1]
        else :
            row += PoUnitGtk.po_diff.prev_page - 1
        return (side, row)

    def copy_button_release_event_cb(self, widget, data=None) :
        (side, row) = self.find_frame_pos(widget)
        if (self.po_diff is not None) :
            poUnit = self.po_diff.unit_dict[(side, row)]
            self.po_diff.merge_from(side, row, poUnit.index, poUnit.unit, poUnit.plural)
    
    def insert_text_event_cb(self, textbuffer, iter, text, length, user_param1=None) :
        if self.unit_change : return
        (side, row) = self.find_frame_pos(user_param1)
        poUnit = self.po_diff.unit_dict[(side, row)]
        self.po_diff.dirty[side] = True
        poUnit.unit.settarget(textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter()))
        self.po_diff.on_dirty()
        # event is before insert has happened
#        end_iter = iter.copy()
#        end_iter.forward_chars(length)
#        textbuffer.apply_tag_by_name("edit", iter, iter)
    
    def changed_event_cb(self, textbuffer, user_param1=None) :
        if self.unit_change : return
        (side, row) = self.find_frame_pos(user_param1)
        poUnit = self.po_diff.unit_dict[(side, row)]
        self.po_diff.dirty[side] = True
        poUnit.unit.settarget(textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter()))
        self.po_diff.on_dirty()
        
    def delete_range_event_cb(self, textbuffer, start, end, user_param1=None) :
        if self.unit_change : return
        (side, row) = self.find_frame_pos(user_param1)
        poUnit = self.po_diff.unit_dict[(side, row)]
        self.po_diff.dirty[side] = True
        poUnit.unit.settarget(textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter()))
        self.po_diff.on_dirty()
        # the event seems to be before the change, so we can't modify it
        #textbuffer.apply_tag_by_name("edit", start, end)
        
    def find_in_buffer(self, view, text_buffer, text, case_sensitive, backwards, bounds) :
        haystack = text_buffer.get_text(bounds[0], bounds[1])
        if not case_sensitive : haystack = haystack.lower()
        offset = len(text_buffer.get_text(text_buffer.get_start_iter(), bounds[0]))
        if backwards :
            index = haystack.rfind(text)
            if (index < 0) : return False
            bound = text_buffer.get_iter_at_offset(offset + index + len(text))
            ins = text_buffer.get_iter_at_offset(offset + index)
        else :
            index = haystack.find(text)
            if (index < 0) : return False
            ins = text_buffer.get_iter_at_offset(offset + index + len(text))
            bound = text_buffer.get_iter_at_offset(offset + index)
        text_buffer.select_range(ins, bound)
        side, row = PoUnitGtk.find_frame_pos(view)
        self.po_diff.builder.get_object("toolbuttonFilterResolved").set_active(False)
        sb = self.po_diff.builder.get_object("unitVscrollbar")
        if (sb.get_value() > row or sb.get_value() + PoDiffGtk.UNITS_PER_PAGE <= row) :
            sb.set_value(row)
        view.grab_focus()
        if view.get_editable() :
            self.po_diff.builder.get_object("replaceButton").set_sensitive(True)
        else :
            self.po_diff.builder.get_object("replaceButton").set_sensitive(False)
        return True

    def find(self, text, use_context, use_msgid, use_translation, case_sensitive, backwards, focus) :
        started = False
        if (not isinstance(focus, gtk.TextView)) :
            started = True
        text_data = []
        if (use_context) : text_data.append([self.context, self.context_buffer])
        if (use_msgid) : text_data.append([self.source, self.source_buffer])
        if (use_translation) : text_data.append([self.target, self.target_buffer])
        if (backwards) : text_data.reverse()
        for view, text_buffer in text_data :
            bounds = [text_buffer.get_start_iter(), text_buffer.get_end_iter()] 
            if view.is_focus() :
                started = True
                if (backwards) :
                    bounds[1] = text_buffer.get_iter_at_mark(text_buffer.get_insert())
                else :
                    bounds[0] = text_buffer.get_iter_at_mark(text_buffer.get_insert())
            if not started : continue
            if self.find_in_buffer(view, text_buffer, text, case_sensitive, backwards, bounds) : return True
        return False

class PoDiffGtk (PoDiff):
    version = "0.0.1"
    title_ids = ["baseTitle","diffTitleA", "diffTitleB", "mergeTitle"]
    UNITS_PER_PAGE = 4
    CONFIG_DIR = "~/.config/podiff"
    CONFIG_FILENAME= "podiff.conf"
    def __init__(self):
        PoDiff.__init__(self)
        self.builder = gtk.Builder()
        self.builder.set_translation_domain(GETTEXT_DOMAIN)
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "podiff.glade"))
        self.builder.connect_signals(self)
        self.diff_table = self.builder.get_object("diffTable")
        self.unit_dict = {}
        self.win = self.builder.get_object("poDiffWindow")
        self.win.show()    
        PoUnitGtk.po_diff = self
        self.dirty = [False, False, False, False]
        self.prev_page = 0
        self.stores = []
        self.clear()
        self.scrolling = False
        self.search_iter = None
        self.unit_frames = {}
        self.config = ConfigParser.ConfigParser()
        try :
            config_filename = os.path.expanduser(os.path.join(PoDiffGtk.CONFIG_DIR, PoDiffGtk.CONFIG_FILENAME))
            self.config.read([config_filename])
            if self.config.has_option("gui", "units_per_page") :
                 PoDiffGtk.UNITS_PER_PAGE = self.config.getint("gui", "units_per_page")
            else :
                if not self.config.has_section("gui") :
                    self.config.add_section("gui")
                self.config.set("gui", "units_per_page", PoDiffGtk.UNITS_PER_PAGE)
                if not os.path.isdir(os.path.expanduser(PoDiffGtk.CONFIG_DIR)) :
                    os.makedirs(os.path.expanduser(PoDiffGtk.CONFIG_DIR))
                with open(os.path.expanduser(config_filename), 'ab') as configfile:
                    self.config.write(configfile)
        except Exception as e:
            print "Error reading config file: " + str(e)

    def main(self):
        gtk.main()

    def delete_event(self, widget, event, data=None):
        if (sum(self.dirty)) :
            msg = gtk.MessageDialog(self.win, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION,
                gtk.BUTTONS_YES_NO, _("Save changes?"))
            response = msg.run()
            if (response == gtk.RESPONSE_YES) :
                for i in range(len(self.dirty)) :
                    if self.dirty[i] :                        
                        self.stores[i].save()
                        print _("Saved {0}").format(self.stores[i].filename)
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def quitMenuItem_button_release_event_cb(self, widget, data=None):
        gtk.main_quit()
        
    def page_range(self, value=None) :
        sb = self.builder.get_object("unitVscrollbar")
        if value is None : value = int(sb.get_value())
        min_visible_row = value
        max_visible_row = value + PoDiffGtk.UNITS_PER_PAGE
        # The get method is only available in PyGTK >= 2.14
#        if (max_visible_row > sb.get_adjustment().get_upper()):
#            max_visible_row = int(sb.get_adjustment().get_upper())
        if (max_visible_row > sb.get_adjustment().upper):
            max_visible_row = int(sb.get_adjustment().upper)
            min_visible_row = max(0, max_visible_row - PoDiffGtk.UNITS_PER_PAGE)
        return (min_visible_row, max_visible_row)

    def show_row(self, visible_row, row) :
        for col in range(0,4) :
            if (col, visible_row) not in self.unit_frames : continue
            unit_frame = self.unit_frames[(col, visible_row)]
            if ((col, row) in self.unit_dict):
                unit_data = self.unit_dict[(col, row)]
                unit_frame.set_unit(unit_data)
                unit_frame.frame.show()
            else:
                unit_frame.frame.hide()
    
    def show_side(self, side, row, index, unit, cf_units, modified, state, plural) :
        shown = False
#        if (side,row) in self.unit_dict:
#            self.diff_table.remove(self.unit_dict[(side, row)].frame)
#            shown = self.unit_dict[(side, row)].frame
#            del self.unit_dict[(side, row)]
        #diff = PoUnitGtk(side, state, plural)
        diff = PoUnitData(index, unit, cf_units, state, plural)
        self.unit_dict[(side, row)] = diff
        #self.diff_table.attach(diff.frame, left_attach=side, right_attach=side+1, top_attach=row+1, bottom_attach=row+2, xoptions=gtk.EXPAND|gtk.FILL|gtk.SHRINK, yoptions=gtk.EXPAND|gtk.FILL|gtk.SHRINK)
        #diff.set_unit(index, unit, cf_unit, modified)
        sb = self.builder.get_object("unitVscrollbar")
        min_visible_row, max_visible_row = self.page_range()
        if self.builder.get_object("toolbuttonFilterResolved").get_active() :
            if row in self.unresolved :
                i = self.unresolved.index(row)
                if (i >= min_visible_row and i < max_visible_row) :
                    self.show_row(i - min_visible_row, row)
        else :
            if (row >= min_visible_row and row < max_visible_row) :
                self.show_row(row - min_visible_row, row)

    def set_total_units(self, row_count) :
        self.unit_count = row_count
        self.hide_units()
        sb = self.builder.get_object("unitVscrollbar")
        sb.set_adjustment(gtk.Adjustment(0, 0, row_count, 1, PoDiffGtk.UNITS_PER_PAGE, PoDiffGtk.UNITS_PER_PAGE))
        #sb.set_increments(1, PoDiffGtk.UNITS_PER_PAGE)
        #sb.set_range(0, row_count)
        #sb.set_value(0)
        self.show_units(0)
        
    def get_unit_count(self):
        return self.unit_count;
    
    def hide_units(self, filter_resolved = None) :
        pass
        
#        min_show, max_show = self.page_range(self.prev_page)
        # print "hide ", min_show, max_show
#        if filter_resolved is None :
#            filter_resolved = self.builder.get_object("toolbuttonFilterResolved").get_active()
#        if filter_resolved :
#            for i in range(min_show, max_show) :
#                row = self.unresolved[i]
#                for col in range(0,4) :
#                    key = (col, row)
#                    if key in self.unit_dict :
#                        self.unit_dict[(col, row)].frame.hide()
#        else :
#            for row in range(min_show, max_show) :
#                for col in range(0,4) :
#                    key = (col, row)
#                    if key in self.unit_dict :
#                        self.unit_dict[(col, row)].frame.hide()

    def is_filtered(self) :
        return self.builder.get_object("toolbuttonFilterResolved").get_active()

    def show_units(self, value) :
        min_show, max_show = self.page_range(int(value))
        # print "show ", min_show, max_show
        if self.is_filtered() :
            for i in range(min_show, max_show) :
                row = self.unresolved[i]
                self.show_row(i - min_show, row)
#                for col in range(0,4) :
#                    key = (col, row)
#                    if key in self.unit_dict :
#                        self.unit_dict[(col, row)].frame.show()
        else :
            for row in range(min_show, max_show) :
                self.show_row(row - min_show, row)
#                for col in range(0,4) :
#                    key = (col, row)
#                    if key in self.unit_dict :
#                        self.unit_dict[(col, row)].frame.show()
        self.prev_page = value
        return True    

    def unitVscrollbar_value_changed_cb(self, widget, data=None) :
        if self.scrolling :
            print "already scrolling"
            return False
        else :
            self.scrolling = True
            # print "scrollbar value changed" + str(widget.get_value())
            self.hide_units()
            self.show_units(int(widget.get_value()))
            self.scrolling = False
        return True # prevent propagation

    def show_status(self, msg) :
        statusbar = self.builder.get_object("statusbar")
        statusbar.pop(1)
        statusbar.push(1, msg)
    
    def show_warning(self, msg) :
        """Display a warning message to the user"""
        print >> sys.stderr, msg
        msg_dialog = gtk.MessageDialog(self.win, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
                gtk.BUTTONS_OK, msg)
        response = msg_dialog.run()
        if (response == gtk.RESPONSE_OK) :
            msg_dialog.hide()

    def set_diff_titles(self, a, b) :
        """Set Titles for diff mode and initialize unit table"""
        t = self.builder.get_object("diffTitleA")
        t.set_text(a)
        t.set_tooltip_text(a)
        t = self.builder.get_object("diffTitleB")
        t.set_text(b)
        t.set_tooltip_text(b)
        t = self.builder.get_object("baseTitle")
        t.hide()
        t = self.builder.get_object("mergeTitle")
        t.hide()        
        self.init_unit_frames(range(1,3), UnitState.MODE_DIFF)

    def set_merge_titles(self, base, a, b, merge) :
        """Set Titles for merge mode and initialize unit table"""
        self.builder.get_object("toolbuttonFilterResolved").set_sensitive(True)
        for label, text in zip(self.title_ids, [base, a, b, merge]):
            t = self.builder.get_object(label)
            t.set_text(text)
            t.set_tooltip_text(text)
            t.show()
        self.init_unit_frames(range(0,4), UnitState.MODE_MERGE)
            
    def init_unit_frames(self, cols, mode) :
#        self.diff_table.foreach(self.diff_table.remove)
        for unit_frame in self.unit_frames.itervalues() :
            self.diff_table.remove(unit_frame.frame)
        self.unit_frames = {}
        for col in cols:
            for row in range(0, PoDiffGtk.UNITS_PER_PAGE) :
                unit_frame = PoUnitGtk(col, UnitState.MODE_MERGE)
                self.unit_frames[(col, row)] = unit_frame
                self.diff_table.attach(unit_frame.frame, col, col+1, row+1, row+2, xoptions=gtk.EXPAND|gtk.FILL|gtk.SHRINK, yoptions=gtk.EXPAND|gtk.FILL|gtk.SHRINK)

    def saveMenuItem_button_release_event_cb(self, widget, data=None):
        self.saveAll()

    def saveAll(self) :
        for i in range(len(self.dirty)) :
            if self.dirty[i] :
                self.stores[i].save()
                self.dirty[i] = False
        self.on_dirty()
    
    def openMenuItem_button_release_event_cb(self, widget, data=None):
        self.openFileDialog()

    def openFileDialog(self) :
        dialog = self.builder.get_object("openDialog")
        if (len(self.stores) == 2) :
            self.builder.get_object("radiobuttonDiff").set_active(True)
            self.builder.get_object("filechooserbuttonA").set_filename(self.stores[Side.LEFT].filename)
            self.builder.get_object("filechooserbuttonB").set_filename(self.stores[Side.RIGHT].filename)
        else :
            if (len(self.stores) == 4) :
                self.builder.get_object("radiobuttonMerge").set_active(True)
                self.builder.get_object("filechooserbuttonBase").set_filename(self.stores[Side.BASE].filename)
                self.builder.get_object("filechooserbuttonA").set_filename(self.stores[Side.A].filename)
                self.builder.get_object("filechooserbuttonB").set_filename(self.stores[Side.B].filename)
                self.builder.get_object("filechooserbuttonMerge").set_filename(self.stores[Side.MERGE].filename)
                
        response = dialog.run()
        dialog.hide()
        if (response > 0):
            base = self.builder.get_object("filechooserbuttonBase").get_filename()
            fileA = self.builder.get_object("filechooserbuttonA").get_filename()
            fileB = self.builder.get_object("filechooserbuttonB").get_filename()
            merge = self.builder.get_object("filechooserbuttonMerge").get_filename()
            # files should have already been checked by OK button release even callback
            if (base is None):
                self.diff(fileA, fileB)
            else :
                self.merge(base, fileA, fileB, merge)

    def openOkButton_button_release_event_cb(self, widget, data=None):
        if (self.builder.get_object("filechooserbuttonA").get_filename() is None or
            self.builder.get_object("filechooserbuttonB").get_filename() is None):
            return True
        if (self.builder.get_object("radiobuttonMerge").get_active()):
            if (self.builder.get_object("filechooserbuttonBase").get_filename() is None or
            self.builder.get_object("filechooserbuttonMerge").get_filename() is None):
                return True
        widget.get_toplevel().response(1)

    def openCancelButton_button_release_event_cb(self, widget, data=None):
        widget.get_toplevel().response(-1)
    
    def radiobuttonDiff_toggled_cb(self, widget, data=None):
        if (widget.get_active()) :
            self.builder.get_object("baseFileLabel").hide()
            self.builder.get_object("mergeFileLabel").hide()
            self.builder.get_object("filechooserbuttonBase").hide()
            self.builder.get_object("filechooserbuttonMerge").hide()
    
    def radiobuttonMerge_toggled_cb(self, widget, data=None):
        if (widget.get_active()) :
            self.builder.get_object("baseFileLabel").show()
            self.builder.get_object("mergeFileLabel").show()
            self.builder.get_object("filechooserbuttonBase").show()
            self.builder.get_object("filechooserbuttonMerge").show()

    def aboutDialogClose(self, widget, res):
        if res == gtk.RESPONSE_CANCEL:
            widget.hide()
    
    def aboutMenuitem_button_release_event_cb(self, widget, data=None):
        dialog = gtk.AboutDialog()
        icon = gtk.gdk.pixbuf_new_from_file("podiff.xpm")
        dialog.set_icon(icon)
        dialog.set_logo(icon)
        dialog.set_name(_("podiffgtk"))
        dialog.set_license(_("""GNU General Public License 
as published by the Free Software Foundation; 
either version 2 of the License, or (at your option) 
any later version.
http://www.gnu.org/licenses/"""))
        dialog.set_website("http://www.thanlwinsoft.org/")
        dialog.set_website_label("ThanLwinSoft.org")
        dialog.set_version(self.version)
        dialog.set_copyright("Keith Stribley 2009")
        dialog.set_authors(["Keith Stribley"])
        dialog.set_program_name(_("PODiffGtk"))
        dialog.set_comments(_("A program to compare two PO files"))
        dialog.connect("response", self.aboutDialogClose)
        dialog.run()
    
    def on_dirty(self) :
        """Checks whether any of the files have changed since being loaded & updates titles accordingly."""
        is_dirty = False
        for i in range(len(self.dirty)) :
            t = self.builder.get_object(self.title_ids[i])
            old_title = t.get_text()
            if len(old_title) > 1 :
                if self.dirty[i] :
                    is_dirty = True
                    if (old_title[0] != '*') : t.set_text("*" + old_title)
                else :
                    if (old_title[0] == '*') : t.set_text(old_title[1:])
        win = self.builder.get_object("poDiffWindow")
        old_title = win.get_title()
        if (is_dirty) :
            if (old_title[0] != '*') :
                win.set_title("*" + old_title)
        else :
            if (old_title[0] == '*') :
                win.set_title(old_title[1:])
                
    def clear(self) :
        super(PoDiffGtk, self).clear()
        for child in self.diff_table.get_children() :
            if (isinstance(child, PoUnitGtk)) :
                self.diff_table.remove(child)
        self.unit_dict = {}
        self.search_iter = None
        self.builder.get_object("toolbuttonFilterResolved").set_active(False)
        self.builder.get_object("toolbuttonFilterResolved").set_sensitive(False)

    def toolbuttonOpen_clicked_cb(self, button, user=None) :
        self.openFileDialog()

    def toolbuttonOpen_button_release_event_cb(self, button, user=None) :
        self.openFileDialog()
        
    def toolbuttonSave_button_release_event_cb(self, button, user=None) :
        self.saveAll()
    
    def toolbuttonSave_clicked_cb(self, button, user=None) :
        self.saveAll()

    def toolbuttonFilterResolved_toggled_cb(self, button, user=None) :
        if len(self.stores) == 4 :
            if (button.get_active()) : 
                self.hide_units(False)
                # update the self.unresolved array
                for resolve in self.resolved :
                    self.unresolved.remove(resolve)
                self.resolved = []
                sb = self.builder.get_object("unitVscrollbar")
                sb.set_adjustment(gtk.Adjustment(0, 0, len(self.unresolved), 1, PoDiffGtk.UNITS_PER_PAGE, PoDiffGtk.UNITS_PER_PAGE))
                self.show_units(0)
            else :
                self.hide_units(True)
                sb = self.builder.get_object("unitVscrollbar")
                sb.set_adjustment(gtk.Adjustment(0, 0, self.unit_count, 1, PoDiffGtk.UNITS_PER_PAGE, PoDiffGtk.UNITS_PER_PAGE))
                self.show_units(0)

    def unitVscrollbar_button_press_event_cb(self, widget, event, data=None) :
        return False
    
    def unitVscrollbar_scroll_event_cb(self, widget, event, data=None) :
        sb = self.builder.get_object("unitVscrollbar")
        # print str(event)
        if (event.direction == gtk.gdk.SCROLL_UP) : 
            sb.set_value(sb.get_value() - sb.get_adjustment().step_increment)        
#            sb.set_value(sb.get_value() - sb.get_adjustment().get_step_increment())
            return True
        if (event.direction & gtk.gdk.SCROLL_DOWN) :
            sb.set_value(sb.get_value() + sb.get_adjustment().step_increment)
#            sb.set_value(sb.get_value() + sb.get_adjustment().get_step_increment())
            return True

    def menuitemSearch_button_release_event_cb(self, button, data=None) :
        dialog = self.builder.get_object("searchDialog")
        dialog.present()

    def closeButton_clicked_cb(self, button, data=None) :
        dialog = self.builder.get_object("searchDialog")
        dialog.hide()
        
    def make_row_visible(self, row) :
        """Make the specified row visible, scrolling the view if needed. 
        Returns index of row in current view."""
        if self.is_filtered() :
            filtered_index = self.unresolved.index(row)
            visible = filtered_index - self.prev_page
            if (visible < 0 or visible >= PoDiffGtk.UNITS_PER_PAGE) :
                self.show_units(filtered_index)
                visible = 0
        else :
            visible = row - self.prev_page
            if (visible < 0 or visible >= PoDiffGtk.UNITS_PER_PAGE) :
                self.show_units(row)
                visible = 0
        return visible

    def search(self) :
        """Search for a string within the units, starting at currently selected unit."""
        if self.unit_count == 0 : return False
        search_combo = self.builder.get_object("searchComboboxentry")
        text = unicode(search_combo.get_active_text())
        use_context = self.builder.get_object("checkbuttonContext").get_active()
        use_msgid = self.builder.get_object("checkbuttonMsgid").get_active()
        use_translation = self.builder.get_object("checkbuttonTranslation").get_active()
        case_sensitive = self.builder.get_object("checkbuttonCase").get_active()
        backwards = self.builder.get_object("checkbuttonBackwards").get_active()
        return self.do_search(text, use_context, use_msgid, use_translation, case_sensitive, backwards, search_combo)

    def do_search(self, text, use_context, use_msgid, use_translation, case_sensitive, backwards, search_combo):
        if not (use_context or use_msgid or use_translation) :
            self.show_warning(_("Nothing to search. Please select the fields which you want to search."))
            return False
        if not case_sensitive :
            text = text.lower()
        if backwards : step = -1
        else : step = 1
        focus = self.win.get_focus()
        from_unit = PoUnitGtk.find_frame_pos(focus)
        if (from_unit is None) :
            from_unit = (0, 0)
            side = Side.BASE
            row = 0
        else :
            side, row = from_unit
            # it must be visible, so try to find the corresponding PoUnitGtk
            if self.is_filtered() :
                visible = self.unresolved.index(row) - self.prev_page
            else:
                visible = row - self.prev_page
            unit_frame = self.unit_frames[(side, visible)]
            if unit_frame.find(text, use_context, use_msgid, use_translation, case_sensitive, backwards, focus) :
                # the word was found, so add it to combo list of previous searches
                if search_combo is not None:
                    ai = search_combo.get_active_iter()
                    if ai is None :
                        search_combo.prepend_text(text)
                        search_combo.set_active_iter(search_combo.get_model().get_iter_first())
                return True
                
        while (True) :
            if (side, row)  in self.unit_dict :
                unit_data = self.unit_dict[(side, row)]
                found = unit_data.find(text, use_context, use_msgid, use_translation, case_sensitive, backwards)
                if found is not None:
                    # find or activate the unit
                    visible_row = self.make_row_visible(row)
                    unit_frame = self.unit_frames[(side, visible_row)]
                    # TODO avoid doing the search twice, since unit_data.find gives us the position info
                    if unit_frame.find(text, use_context, use_msgid, use_translation, case_sensitive, backwards, focus) :
                        # print "Found at ", text, side, row
                        # the word was found, so add it to combo list of previous searches
                        if search_combo is not None:
                            ai = search_combo.get_active_iter()
                            if ai is None :
                                search_combo.prepend_text(text)
                                search_combo.set_active_iter(search_combo.get_model().get_iter_first())
                        return True
                    else :
                        print "Not found in PoUnitGtk at " + str(side) + "," + str(row) 
                        #assert(False) # shoundn't happen
            side += step
            if (side < 0) :
                side = Side.MERGE
                row += step
            else :
                if side > Side.MERGE :
                    side = Side.BASE
                    row += step
            if (row < 0) : row = self.unit_count - 1
            if (row >= self.unit_count) : row = 0
            focus = None
            if (from_unit == (side, row)) : break
        print "Nothing found"
        return False

    def replace(self) :
        search_combo = self.builder.get_object("searchComboboxentry")
        replace_combo = self.builder.get_object("replaceComboboxentry")
        text = unicode(search_combo.get_active_text())
        replacement = unicode(replace_combo.get_active_text())
        case_sensitive = self.builder.get_object("checkbuttonCase").get_active()
        return self.do_replace(text, replacement, case_sensitive, replace_combo)
        
    def do_replace(self, text, replacement, case_sensitive, replace_combo):
        if not case_sensitive : text = text.lower()
        focus = self.win.get_focus()
        from_unit = PoUnitGtk.find_frame_pos(focus)
        if from_unit is not None and isinstance(focus, gtk.TextView) and focus.get_editable():
            text_buffer = focus.get_buffer()
            start = text_buffer.get_iter_at_mark(text_buffer.get_insert())
            end = text_buffer.get_iter_at_mark(text_buffer.get_selection_bound())
            selected = text_buffer.get_text(start, end)
            if not case_sensitive :
                selected = selected.lower()
            if unicode(selected) == text :
#                text_buffer.delete_selection(True, True)
                text_buffer.delete_interactive(start, end, True)
                text_buffer.insert_interactive_at_cursor(replacement, True)
                if replace_combo is not None :
                    ai = replace_combo.get_active_iter()
                    if ai is None :
                        replace_combo.prepend_text(replacement)
                        replace_combo.set_active_iter(replace_combo.get_model().get_iter_first())    
                return True
        return False

    def searchButton_clicked_cb(self, button, data=None) :
        try :
            self.search()
        except Exception as e:
            print "Exception occured during search: " + str(e)
            tb = sys.exc_traceback
            while tb is not None :
                print _("{0} line {1}\t in {2}").format(tb.tb_frame.f_code.co_filename, tb.tb_lineno, tb.tb_frame.f_code.co_name)
                tb = tb.tb_next

    def toolbuttonSearch_clicked_cb(self, button, data=None) :
        return self.menuitemSearch_button_release_event_cb(button, data)
        
    def replaceButton_clicked_cb(self, button, data=None) :
        if not self.replace() :
            self.search() and self.replace()
        
    def searchDialog_focus_in_event_cb(self, widget, data=None) :
        dialog = self.builder.get_object("searchDialog")
        dialog.set_opacity(1.0)

    def searchDialog_focus_out_event_cb(self, widget, data=None) :
        dialog = self.builder.get_object("searchDialog")
        dialog.set_opacity(0.7)

    def checkbuttonTranslation_toggled_cb(self, widget, data=None):
        if widget.get_active() :
            self.builder.get_object("replaceComboboxentry").set_sensitive(True)
        else :
            self.builder.get_object("replaceComboboxentry").set_sensitive(False)

    def editMenuItem_activate_cb(self, menu, data=None) :
        focus = self.win.get_focus()
        if isinstance(focus, gtk.TextView):
            if focus.get_buffer().get_has_selection() :
                self.builder.get_object("imagemenuitemCopy").set_sensitive(True)
            else :
                self.builder.get_object("imagemenuitemCopy").set_sensitive(False)
            if focus.get_editable() :
                self.builder.get_object("imagemenuitemPaste").set_sensitive(True)
                if focus.get_buffer().get_has_selection() :
                    self.builder.get_object("imagemenuitemCut").set_sensitive(True)
                    self.builder.get_object("imagemenuitemDelete").set_sensitive(True)
                else :
                    self.builder.get_object("imagemenuitemCut").set_sensitive(False)
                    self.builder.get_object("imagemenuitemDelete").set_sensitive(False)                    
            else :
                self.builder.get_object("imagemenuitemCut").set_sensitive(False)
                self.builder.get_object("imagemenuitemDelete").set_sensitive(False)
                self.builder.get_object("imagemenuitemPaste").set_sensitive(False)
        else :
            self.builder.get_object("imagemenuitemCopy").set_sensitive(False)
            self.builder.get_object("imagemenuitemCut").set_sensitive(False)
            self.builder.get_object("imagemenuitemDelete").set_sensitive(False)
            self.builder.get_object("imagemenuitemPaste").set_sensitive(False)

    def imagemenuitemDelete_activate_cb(self, menu, data=None) :
        focus = self.win.get_focus()
        if isinstance(focus, gtk.TextView) and focus.get_editable():
            focus.get_buffer().delete_selection(True, True)

    def imagemenuitemCut_activate_cb(self, menu, data=None) :
        focus = self.win.get_focus()
        if isinstance(focus, gtk.TextView) and focus.get_editable():
            focus.get_buffer().cut_clipboard(gtk.Clipboard(), True)

    def imagemenuitemCopy_activate_cb(self, menu, data=None) :
        print "toggle copy"
        focus = self.win.get_focus()
        if isinstance(focus, gtk.TextView):
            focus.get_buffer().copy_clipboard(gtk.Clipboard())
        print str(focus)
    
    def imagemenuitemPaste_activate_cb(self, menu, data=None) :
        focus = self.win.get_focus()
        if isinstance(focus, gtk.TextView) and focus.get_editable():
            focus.get_buffer().paste_clipboard(gtk.Clipboard(), None, True)

    def viewMenuItem_activate_cb(self, menu, data=None) :
        active = self.builder.get_object("toolbuttonFilterResolved").get_active()
        menuitem = self.builder.get_object("menuitemFilterResolved")
        menuitem.set_active(active)
        if len(self.stores) == 4 :
            menuitem.set_sensitive(True)
        else :
            menuitem.set_sensitive(False)

    def menuitemFilterResolved_toggled_cb(self, menu, data=None) :
        self.builder.get_object("toolbuttonFilterResolved").set_active(menu.get_active())

# main method
if __name__ == "__main__":
    base = PoDiffGtk()
    if (len(sys.argv) == 3) :
        base.diff(sys.argv[1], sys.argv[2])
    else :
        if  len(sys.argv) == 5 :
            base.merge(sys.argv[1], sys.argv[2],sys.argv[3], sys.argv[4])
        else :
            if (len(sys.argv) != 1):
                print _("Usage: {0} fileA fileB").format(sys.argv[0])
                print _("or     {0} base fileA fileB merge-output").format(sys.argv[0])
                print _("or     {0}").format(sys.argv[0])
                sys.exit(1)
    base.main()


