#!/usr/bin/python
import pygtk
pygtk.require('2.0')
import gtk
import sys
import translate.storage.factory

class Side : LEFT, RIGHT = (0, 1)

class PoUnitGtk(object) :
	def __init__(self, side):
		self.side = side
		self.frame = gtk.Frame()
		self.frame.set_size_request(250, -1)
		self.vbox = gtk.VBox(False, 2)
		self.title_box = gtk.HBox()
		self.copy_button = gtk.Button()
		self.source = gtk.TextView()
		self.source.set_wrap_mode(gtk.WRAP_WORD)
		self.source_buffer = gtk.TextBuffer()
		self.source_buffer.set_text("Source")
		self.source.set_tooltip_text("Source")
		self.source.set_buffer(self.source_buffer)
		self.source.show()
		self.target = gtk.TextView()
		self.target_buffer = gtk.TextBuffer()
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

		if (self.side == Side.LEFT): 
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

	def set_unit(self, unit) :
#		self.source_buffer.set_text(unit.getid())
#		self.target_buffer.set_text(unit.gettarget())
		self.source_buffer.set_text(unit.source)
		self.target_buffer.set_text(unit.gettarget())
		self.context_buffer.set_text(unit.getcontext())
		if len(unit.getcontext()) > 0 :
			self.context.show()
		else :
			self.context.hide()

class PoDiffGtk (object):
	def __init__(self):
		self.builder = gtk.Builder()
		self.builder.add_from_file("podiff.glade")
		self.builder.connect_signals(self)
		self.diff_table = self.builder.get_object("diffTable")
		win = self.builder.get_object("poDiffWindow")
		win.show()	

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
		
	def __show_left(self, row, unit) :
		diff = PoUnitGtk(Side.LEFT)
		diff.set_unit(unit)
		self.diff_table.attach(diff.frame, left_attach=0, right_attach=1, top_attach=row, bottom_attach=row+1)
		diff.frame.show()

	def __show_right(self, row, unit) :
		diff = PoUnitGtk(Side.RIGHT)
		diff.set_unit(unit)
		self.diff_table.attach(diff.frame, left_attach=1, right_attach=2, top_attach=row, bottom_attach=row+1)
		diff.frame.show()

	def diff(self, a, b) :
		self.stores = []
		self.stores.append(translate.storage.factory.getobject(a))
		self.stores.append(translate.storage.factory.getobject(b))
		row = 0
		alternateTranslations = 0
		aOnly = 0
		bOnly = 0
		# iterate over left hand side
		for i in self.stores[0].unit_iter():
			bUnit = self.stores[1].findunit(i.source)
			if (bUnit is not None) :
				if (i.gettarget() != bUnit.gettarget()): # a and b different
					self.__show_left(row, i)
					self.__show_right(row, bUnit)
					row+=1
					alternateTranslations+=1
			else : # a only
				self.__show_left(row, i)
				row+=1
				aOnly+=1

		for i in self.stores[1].unit_iter():
			a = self.stores[0].findunit(i.source)
			if a is None : # b only
				self.__show_right(row, i)
				row+=1
				bOnly+=1
		msg = "{0} differences, {1} only in a, {2} only in b".format(alternateTranslations, aOnly, bOnly)
		self.builder.get_object("statusLabel").set_text(msg)
		print >> sys.stderr, "" + str(alternateTranslations) + " differences"
		print >> sys.stderr, "" + str(aOnly) + " only in a"
		print >> sys.stderr, "" + str(bOnly) + " only in b"

#if gtk.init_check() :
if __name__ == "__main__":
    base = PoDiffGtk()
    if (len(sys.argv) >= 3) :
    	base.diff(sys.argv[1], sys.argv[2])
    base.main()

