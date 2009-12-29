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
import translate.storage.factory
import translate.storage.pypo

class Side : LEFT, RIGHT = (0, 1)

class PODiff(object) :
	copy_notes = True

	def __init__(self) :
		self.dirty = [False, False]

	def diff(self, a, b) :
		self.stores = []
		self.stores.append(translate.storage.factory.getobject(a))
		self.stores.append(translate.storage.factory.getobject(b))
		self.set_titles(a, b)
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
		
	def merge_from(self, from_side, from_row, from_unit) :
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


