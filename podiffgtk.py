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
import translate.storage.factory

import podiff
from textdiff import find_matches

class PoUnitGtk(object) :
    """Displays a frame showing the contents of a translatable unit."""
    po_diff = None
    diff_colors = [gtk.gdk.Color(1.0,0.5,0.5), gtk.gdk.Color(0.5,1.0,0.5), gtk.gdk.Color(0.5,0.5,1.0), gtk.gdk.Color(1.0,1.0,0.5), gtk.gdk.Color(1.0,0.5,1.0), gtk.gdk.Color(0.5,1.0,1.0), gtk.gdk.Color(0.5,0.5,0.5)]
    def __init__(self, side, state):
        self.side = side
        self.frame = gtk.Frame()
        self.frame.connect("scroll-event", self.po_diff.unitVscrollbar_scroll_event_cb)
        self.vbox = gtk.VBox(False, 2)
        self.title_box = gtk.HBox()
        self.copy_button = gtk.Button()
        self.copy_button.connect("released", self.copy_button_release_event_cb)
        self.source = gtk.TextView()
        self.source.set_wrap_mode(gtk.WRAP_WORD)
        self.source_buffer = gtk.TextBuffer()
        self.source_buffer.set_text("Source")
        self.source.set_tooltip_text("Source")
        self.source.set_buffer(self.source_buffer)
        self.source.set_editable(False)
        self.source.show()
        self.target = gtk.TextView()
        self.target_buffer = gtk.TextBuffer()
        self.diff_tag = []
        for i in range(3) :
            self.diff_tag.append(gtk.TextTag(name="diff" + str(i)))
            self.diff_tag[i].set_property("background-gdk", self.diff_colors[self.side + i])
#            if (i == 0) : self.diff_tag[i].set_property("style", pango.STYLE_ITALIC)
#            if (i == 1) : self.diff_tag[i].set_property("underline", pango.UNDERLINE_SINGLE)
#            if (i == 2) : self.diff_tag[i].set_property("underline", pango.UNDERLINE_DOUBLE)
            self.target_buffer.get_tag_table().add(self.diff_tag[i])
        self.edit_tag = gtk.TextTag(name="edit")
        self.edit_tag.set_property("background-gdk", self.diff_colors[len(self.diff_colors) - 1])
        self.target_buffer.get_tag_table().add(self.edit_tag)
        self.target_buffer.set_text("Target")
        self.target.set_tooltip_text("Target")
        self.target.set_buffer(self.target_buffer)
        self.target.show()
        self.context = gtk.TextView()
        self.context_buffer = gtk.TextBuffer()
        self.context_buffer.set_text("Context")
        self.context.set_tooltip_text("Context")
        self.context.set_buffer(self.context_buffer)
        self.context.set_editable(False)
        self.context.show()
        self.copy_button.show()

        if (state & podiff.UnitState.MODE_MERGE) :
            self.frame.set_size_request(125, -1)
            if (self.side == podiff.Side.BASE or self.side == podiff.Side.A or self.side == podiff.Side.B) :
                self.copy_button.set_label(">>")
                arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_IN)
                arrow.show()
                self.frame.set_label_align(1.0, .5)
                self.title_box.add(arrow)
                self.title_box.add(self.copy_button)
            else :
                img = gtk.Image()
                if (state & podiff.UnitState.RESOLVED) :
                    img.set_from_file(os.path.dirname(__file__) + "/merged.png")
                else :           
                    img.set_from_file(os.path.dirname(__file__) + "/unmerged.png")
                img.show()             
                self.title_box.add(img)
                self.copy_button.hide()
                pass            
        else :
            self.frame.set_size_request(250, -1)
            if (self.side == podiff.Side.LEFT): 
                self.copy_button.set_label(">>")
                arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_IN)
                arrow.show()
                self.frame.set_label_align(1.0, .5)
                self.title_box.add(arrow)
                self.title_box.add(self.copy_button)
            else :
                self.copy_button.set_label("<<")
                arrow = gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_IN)
                arrow.show()
                self.frame.set_label_align(0.0, .5)
                self.title_box.add(self.copy_button)
                self.title_box.add(arrow)
        self.frame.set_label_widget(self.title_box)
        self.target.set_wrap_mode(gtk.WRAP_WORD)
        self.frame.add(self.vbox)
        self.vbox.add(self.context)
        self.vbox.add(self.source)
        self.vbox.add(self.target)
        self.vbox.show()
        self.title_box.show()

    def set_unit(self, unit, cf_units=None, modified=False) :
#        self.source_buffer.set_text(unit.getid())
#        self.target_buffer.set_text(unit.gettarget())
        self.unit = unit
        self.source_buffer.set_text(unit.source)
        self.target_buffer.set_text(unit.gettarget())
        self.context_buffer.set_text(unit.getcontext())
        self.target_buffer.connect("insert-text", self.insert_text_event_cb, self.target)
        self.target_buffer.connect("delete-range", self.delete_range_event_cb, self.target)
        self.target_buffer.connect("changed", self.changed_event_cb, self.target)
        if len(unit.getcontext()) > 0 :
            self.context.show()
        else :
            self.context.hide()
        self.po_diff.on_dirty()
        if (cf_units is not None) :
            # print unit.gettarget()
            # print cf_unit.gettarget()
            for j in range(len(cf_units)) :
                cf_unit = cf_units[j]
                common = find_matches(unit.gettarget(), cf_unit.gettarget())
                pos = 0
                for i in range(len(common)) :
                    if (pos < common[i][0]) : 
                        s_iter = self.target_buffer.get_iter_at_offset(pos)
                        e_iter = self.target_buffer.get_iter_at_offset(common[i][0])
                        self.target_buffer.apply_tag_by_name("diff" + str(j), s_iter, e_iter)
                    pos = common[i][0] + common[i][2]
                if pos < len(unit.gettarget()) :
                    s_iter = self.target_buffer.get_iter_at_offset(pos)
                    e_iter = self.target_buffer.get_iter_at_offset(len(unit.gettarget()))
                    self.target_buffer.apply_tag_by_name("diff" + str(j), s_iter, e_iter)
        if (modified) :
            self.target_buffer.remove_all_tags(self.target_buffer.get_start_iter(), self.target_buffer.get_end_iter())
            if self.side == podiff.Side.LEFT :
                self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(0.0, 1.0, 0.0))
            else :
                self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(1.0, 0.0, 0.0))
        else :
            self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))

    def find_frame_pos(self, widget) :
        frame = widget.get_parent()
        while (not isinstance(frame, gtk.Frame)) : frame = frame.get_parent()
        side = frame.get_parent().child_get_property(frame, "left-attach")
        row = frame.get_parent().child_get_property(frame, "top-attach")-1
        return (side, row)

    def copy_button_release_event_cb(self, widget, data=None) :
        (side, row) = self.find_frame_pos(widget)
        if (self.po_diff is not None) :
            poUnit = self.po_diff.unit_dict[(side, row)]
            self.po_diff.merge_from(side, row, poUnit.unit)
    
    def insert_text_event_cb(self, textbuffer, iter, text, length, user_param1=None) :
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
        (side, row) = self.find_frame_pos(user_param1)
        poUnit = self.po_diff.unit_dict[(side, row)]
        self.po_diff.dirty[side] = True
        poUnit.unit.settarget(textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter()))
        self.po_diff.on_dirty()
        
    def delete_range_event_cb(self, textbuffer, start, end, user_param1=None) :
        (side, row) = self.find_frame_pos(user_param1)
        poUnit = self.po_diff.unit_dict[(side, row)]
        self.po_diff.dirty[side] = True
        poUnit.unit.settarget(textbuffer.get_text(textbuffer.get_start_iter(), textbuffer.get_end_iter()))
        self.po_diff.on_dirty()
        # the event seems to be before the change, so we can't modify it
        #textbuffer.apply_tag_by_name("edit", start, end)

class PoDiffGtk (podiff.PODiff):
    version = "0.0.1"
    title_ids = ["baseTitle","diffTitleA", "diffTitleB", "mergeTitle"]
    UNITS_PER_PAGE = 5
    def __init__(self):
        podiff.PODiff.__init__(self)
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.dirname(__file__) + "/podiff.glade")
        self.builder.connect_signals(self)
        self.diff_table = self.builder.get_object("diffTable")
        self.unit_dict = {}
        self.win = self.builder.get_object("poDiffWindow")
        self.win.show()    
        PoUnitGtk.po_diff = self
        self.dirty = [False, False, False, False]
        self.prev_page = 0

    def main(self):
        gtk.main()

    def delete_event(self, widget, event, data=None):
        if (sum(self.dirty)) :
            msg = gtk.MessageDialog(self.win, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION,
                gtk.BUTTONS_YES_NO, "Save changes?")
            response = msg.run()
            if (response == gtk.RESPONSE_YES) :
                for i in range(len(self.dirty)) :
                    if self.dirty[i] :                        
                        self.stores[i].save()
                        print "Saved " + self.stores[i].filename
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
        if (max_visible_row > sb.get_adjustment().get_upper()):
            max_visible_row = int(sb.get_adjustment().get_upper())
            min_visible_row = max(0, max_visible_row - PoDiffGtk.UNITS_PER_PAGE)
        return (min_visible_row, max_visible_row)
    
    def show_side(self, side, row, unit, cf_unit = None, modified = False, state=0) :
        shown = False
        if (side,row) in self.unit_dict:
            self.diff_table.remove(self.unit_dict[(side, row)].frame)
            shown = self.unit_dict[(side, row)].frame
            del self.unit_dict[(side, row)]
        diff = PoUnitGtk(side, state)
        self.unit_dict[(side, row)] = diff
        self.diff_table.attach(diff.frame, left_attach=side, right_attach=side+1, top_attach=row+1, bottom_attach=row+2)
        diff.set_unit(unit, cf_unit, modified)
        sb = self.builder.get_object("unitVscrollbar")
        min_visible_row, max_visible_row = self.page_range()
        if self.builder.get_object("toolbuttonFilterResolved").get_active() :
            if row in self.unresolved :
                i = self.unresolved.index(row)
                if (i >= min_visible_row and i < max_visible_row) :
                    diff.frame.show()
        else :
            if (row >= min_visible_row and row < max_visible_row) :
                    diff.frame.show()
        # if (state & podiff.UnitState.AMBIGUOUS) :
        # diff.frame.show()

    def set_total_units(self, row_count) :
        self.unit_count = row_count
        self.hide_units()
        sb = self.builder.get_object("unitVscrollbar")
        sb.set_adjustment(gtk.Adjustment(0, 0, row_count, 1, PoDiffGtk.UNITS_PER_PAGE, PoDiffGtk.UNITS_PER_PAGE))
        #sb.set_increments(1, PoDiffGtk.UNITS_PER_PAGE)
        #sb.set_range(0, row_count)
        #sb.set_value(0)
        self.show_units(0)
    
    def hide_units(self, filter_resolved = None) :
        min_show, max_show = self.page_range(self.prev_page)
        # print "hide ", min_show, max_show
        if filter_resolved is None :
            filter_resolved = self.builder.get_object("toolbuttonFilterResolved").get_active()
        if filter_resolved :
            for i in range(min_show, max_show) :
                row = self.unresolved[i]
                for col in range(0,4) :
                    key = (col, row)
                    if key in self.unit_dict :
                        self.unit_dict[(col, row)].frame.hide()
        else :
            for row in range(min_show, max_show) :
                for col in range(0,4) :
                    key = (col, row)
                    if key in self.unit_dict :
                        self.unit_dict[(col, row)].frame.hide()

    def show_units(self, value) :
        min_show, max_show = self.page_range(int(value))
        # print "show ", min_show, max_show
        filter_resolved = self.builder.get_object("toolbuttonFilterResolved").get_active()
        if filter_resolved :
            for i in range(min_show, max_show) :
                row = self.unresolved[i]
                for col in range(0,4) :
                    key = (col, row)
                    if key in self.unit_dict :
                        self.unit_dict[(col, row)].frame.show()
        else :
            for row in range(min_show, max_show) :
                for col in range(0,4) :
                    key = (col, row)
                    if key in self.unit_dict :
                        self.unit_dict[(col, row)].frame.show()
        self.prev_page = value
        return True    

    def unitVscrollbar_value_changed_cb(self, widget, data=None) :
        self.hide_units()
        return self.show_units(int(widget.get_value()))

    def show_left(self, row, unit, cf_unit = None, modified = False, state=0) :
        self.show_side(podiff.Side.LEFT, row, unit, cf_unit, modified, state)

    def show_right(self, row, unit, cf_unit = None, modified = False, state=0) :
        self.show_side(podiff.Side.RIGHT, row, unit, cf_unit, modified, state)

    def show_status(self, msg) :
        statusbar = self.builder.get_object("statusbar")
        statusbar.pop(1)
        statusbar.push(1, msg)
        
    def set_diff_titles(self, a, b) :
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

    def set_merge_titles(self, base, a, b, merge) :
        for label, text in zip(self.title_ids, [base, a, b, merge]):
            t = self.builder.get_object(label)
            t.set_text(text)
            t.set_tooltip_text(text)
            t.show()

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
            self.builder.get_object("filechooserbuttonA").set_filename(self.stores[podiff.Side.LEFT].filename)
            self.builder.get_object("filechooserbuttonB").set_filename(self.stores[podiff.Side.RIGHT].filename)
        else :
            if (len(self.stores) == 4) :
                self.builder.get_object("radiobuttonMerge").set_active(True)
                self.builder.get_object("filechooserbuttonBase").set_filename(self.stores[podiff.Side.BASE].filename)
                self.builder.get_object("filechooserbuttonA").set_filename(self.stores[podiff.Side.A].filename)
                self.builder.get_object("filechooserbuttonB").set_filename(self.stores[podiff.Side.B].filename)
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
        dialog.set_name("podiffgtk")
        dialog.set_license("""GNU General Public License 
as published by the Free Software Foundation; 
either version 2 of the License, or (at your option) 
any later version.
http://www.gnu.org/licenses/""")
        dialog.set_website("http://www.thanlwinsoft.org/")
        dialog.set_website_label("ThanLwinSoft.org")
        dialog.set_version(self.version)
        dialog.set_copyright("Keith Stribley 2009")
        dialog.set_authors(["Keith Stribley"])
        dialog.set_program_name("PODiffGtk")
        dialog.set_comments("A program to compare two PO files")
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
        self.unit_count = 0
        self.unresolved = []
        for child in self.diff_table.get_children() :
            if (isinstance(child, PoUnitGtk)) :
                self.diff_table.remove(child)
        for i in range(len(self.dirty)) :
            self.dirty[i] = False
        self.unit_dict = {}
        self.builder.get_object("toolbuttonFilterResolved").set_active(False)

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
#        if len(self.stores) == 4 :
#            unresolved = set(self.unresolved)
#            if (button.get_active()) : 
#                for child in self.diff_table.get_children() :
#                    row = self.diff_table.child_get_property(child, "top-attach")
#                    if row not in unresolved:
#                        child.hide()
#            else :
#                for child in self.diff_table.get_children() :
#                    child.show()
    def unitVscrollbar_button_press_event_cb(self, widget, event, data=None) :
        pass
    
    def unitVscrollbar_scroll_event_cb(self, widget, event, data=None) :
        sb = self.builder.get_object("unitVscrollbar")
        #print str(event)
        if (event.direction == gtk.gdk.SCROLL_UP) : 
            sb.set_value(sb.get_value() - sb.get_adjustment().get_step_increment())
        if (event.direction & gtk.gdk.SCROLL_DOWN) : 
            sb.set_value(sb.get_value() + sb.get_adjustment().get_step_increment())

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
                print "Usage: " + sys.argv[0] + " fileA fileB"
                print "or     " + sys.argv[0] + " base fileA fileB merge-output"
                print "or     " + sys.argv[0]
                sys.exit(1)
    base.main()


