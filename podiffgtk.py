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
import sys
import podiff
import textdiff
import translate.storage.factory

class PoUnitGtk(object) :
	"""Displays a frame showing the contents of a translatable unit."""
	po_diff = None
	diff_colors = [gtk.gdk.Color(1.0,0.0,0.0), gtk.gdk.Color(0.0,1.0,0.0), gtk.gdk.Color(0.0,0.0,1.0), gtk.gdk.Color(1.0,1.0,0.0), gtk.gdk.Color(1.0,0.0,1.0), gtk.gdk.Color(0.0,1.0,1.0)]
	def __init__(self, side):
		self.side = side
		self.frame = gtk.Frame()
		self.frame.set_size_request(250, -1)
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
		self.source.show()
		self.target = gtk.TextView()
		self.target_buffer = gtk.TextBuffer()
		self.diff_tag = gtk.TextTag(name="diff")
		self.diff_tag.set_property("background-gdk", self.diff_colors[self.side])
		self.target_buffer.get_tag_table().add(self.diff_tag)
		self.target_buffer.set_text("Target")
		self.target.set_tooltip_text("Target")
		self.target.set_buffer(self.target_buffer)
		self.target.show()
		self.context = gtk.TextView()
		self.context_buffer = gtk.TextBuffer()
		self.context_buffer.set_text("Context")
		self.context.set_tooltip_text("Context")
		self.context.set_buffer(self.context_buffer)
		self.context.show()

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
		self.copy_button.show()
		self.title_box.show()

	def set_unit(self, unit, cf_unit=None, modified=False) :
#		self.source_buffer.set_text(unit.getid())
#		self.target_buffer.set_text(unit.gettarget())
		self.unit = unit
		self.source_buffer.set_text(unit.source)
		self.target_buffer.set_text(unit.gettarget())
		self.context_buffer.set_text(unit.getcontext())
		if len(unit.getcontext()) > 0 :
			self.context.show()
		else :
			self.context.hide()
		self.po_diff.on_dirty()
		if (cf_unit is not None) :
			print unit.gettarget()
			print cf_unit.gettarget()
			common = textdiff.find_deltas(unit.gettarget(), cf_unit.gettarget())
			pos = 0
			for i in range(len(common)) :
				if (pos < common[i][0]) : 
					s_iter = self.target_buffer.get_iter_at_offset(pos)
					e_iter = self.target_buffer.get_iter_at_offset(common[i][0])
					self.target_buffer.apply_tag_by_name("diff", s_iter, e_iter)
				pos = common[i][0] + common[i][2]
		if (modified) :
			self.target_buffer.remove_all_tags(0, self.target_buffer.get_char_count())
			if self.side == podiff.Side.LEFT :
				self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(0.0, 1.0, 0.0))
			else :
				self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(1.0, 0.0, 0.0))
		else :
			self.target.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))
	def copy_button_release_event_cb(self, widget, data=None) :
		frame = widget.get_parent()
		while (not isinstance(frame, gtk.Frame)) : frame = frame.get_parent()
		
		side = frame.get_parent().child_get_property(frame, "left-attach")
		row = frame.get_parent().child_get_property(frame, "top-attach")
		if (self.po_diff is not None) :
			poUnit = self.po_diff.unit_dict[(side, row)]
			self.po_diff.merge_from(side, row, poUnit.unit)

class PoDiffGtk (podiff.PODiff):
	version = "0.0.1"
	def __init__(self):
		podiff.PODiff.__init__(self)
		self.builder = gtk.Builder()
		self.builder.add_from_file("podiff.glade")
		self.builder.connect_signals(self)
		self.diff_table = self.builder.get_object("diffTable")
		self.unit_dict = {}
		self.win = self.builder.get_object("poDiffWindow")
		self.win.show()	
		PoUnitGtk.po_diff = self

	def main(self):
		gtk.main()

	def delete_event(self, widget, event, data=None):
		print "Delete"
		return False

	def destroy(self, widget, data=None):
		print "Destroy"
		gtk.main_quit()

	def quitMenuItem_button_release_event_cb(self, widget, data=None):
		gtk.main_quit()
	
	def show_side(self, side, row, unit, cf_unit = None, modified = False) :
		diff = PoUnitGtk(side)
		diff.set_unit(unit, cf_unit, modified)
		self.diff_table.attach(diff.frame, left_attach=side, right_attach=side+1, top_attach=row, bottom_attach=row+1)
		self.unit_dict[(side, row)] = diff
		diff.frame.show()

	def show_left(self, row, unit, cf_unit = None, modified = False) :
		self.show_side(podiff.Side.LEFT, row, unit, cf_unit, modified)

	def show_right(self, row, unit, cf_unit = None, modified = False) :
		self.show_side(podiff.Side.RIGHT, row, unit, cf_unit, modified)

	def show_status(self, msg) :
		self.builder.get_object("statusLabel").set_text(msg)
		
	def set_titles(self, a, b) :
		t = self.builder.get_object("diffTitle0")
		t.set_text(a)
		t.set_tooltip_text(a)
		t = self.builder.get_object("diffTitle1")
		t.set_text(b)
		t.set_tooltip_text(b)
		
	def saveMenuItem_button_release_event_cb(self, widget, data=None):
		for i in range(len(self.dirty)) :
			if self.dirty[i] :
				self.stores[i].save()
				self.dirty[i] = False
		self.on_dirty()
	
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
			t = self.builder.get_object("diffTitle" + str(i))
			old_title = t.get_text()
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

# main method
if __name__ == "__main__":
    base = PoDiffGtk()
    if (len(sys.argv) >= 3) :
    	base.diff(sys.argv[1], sys.argv[2])
    base.main()

