


import gtk
import string 

class AutoCompleter():

	def __init__(self, view, keywords):

		self.window = gtk.Window(gtk.WINDOW_POPUP)
		self.view = view
		self.setcoords()
		self.handlerId1 = self.view.connect('key_release_event',self.keyrelease)
		self.handlerId2 = self.view.connect('key_press_event',self.keypress)
		self.keywords = keywords

		self.scrolledView = gtk.ScrolledWindow()
		
		self.store = gtk.ListStore(str)

		self.treeview  = gtk.TreeView(self.store)
		self.treeview.set_headers_visible(False)
		renderer   = gtk.CellRendererText()
		self.treeview.insert_column_with_attributes(-1, '', renderer, text=0)
		self.scrolledView.add(self.treeview)

		self.scrolledView.show()
		self.treeview.show()

		self.window.add(self.scrolledView)

		word = self.getWord()		

		for x in self.getSuggestions(word):
			self.store.append([x])

	def keypress(self, widget, event):

		# print(event.keyval)
		if(event.keyval == 65293 or event.keyval == 65289):
			return True
		if(event.keyval in [gtk.keysyms.Down,gtk.keysyms.Up,gtk.keysyms.Left,gtk.keysyms.Right]):
			return True


	def keyrelease(self, widget, event):

		self.setcoords()
		self.window.move(self.x, self.y)
		self.window.show_all()
		# print(event.keyval)
		if(event.keyval == 65293 or event.keyval == 65289):
			print("return press")
			suggestedWord = self.getSelected()
			print("word selected:",suggestedWord)
			self.addWord(suggestedWord)
			self.quit()
			return True

		elif(event.keyval == gtk.keysyms.Down):
			print("down press")
			self.selectionDown()
			return True

		elif(event.keyval == gtk.keysyms.Up):
			print("up press")
			self.selectionUp()			
			return True

		elif(event.keyval == 65307 ):
			print("escape press")
			self.quit()

		elif(event.string in string.printable):
			print("printable press")
			self.store.clear()
			word = self.getWord()
			print(word)
			word = word.strip()
			suggests = self.getSuggestions(word)
			print("suggests:",suggests)
			if(len(suggests) == 0):
				self.quit()
			else:
				for x in self.getSuggestions(word):
					self.store.append([x])
				# self.window.show_all()
	
	def quit(self):
		self.view.disconnect(self.handlerId1)
		self.view.disconnect(self.handlerId2)
		self.window.destroy()

	def getSelected(self):
		selection = self.treeview.get_selection()
		try:
			model,pathlist = selection.get_selected_rows()
			for path in pathlist:
				tree_iter = model.get_iter(path)
				value = model.get_value(tree_iter,0)
				print(tree_iter,value)
				return value
		except:
			print("error")

	def getSelectedIndex(self):
		selection = self.treeview.get_selection()
		model, treeiter = selection.get_selected()
		if treeiter is not None:
		# rowcontents = model[treeiter][0:3]  # for a 4 column treeview
			rownumobj = model.get_path(treeiter)
			print(rownumobj[0])
			return rownumobj[0]
		else:
			return -1
		# 	rownum = int(rownumobj.to_string())
		# 	print("rownum:",rownum)
		# return rownum

	def selectionDown(self):
		row = min(self.getSelectedIndex() + 1, len(self.store) - 1)
		selection = self.treeview.get_selection()
		selection.unselect_all()
		selection.select_path(row)
		self.treeview.scroll_to_cell(row)
		return True

	def selectionUp(self):
		row = max(self.getSelectedIndex() - 1, 0)
		selection = self.treeview.get_selection()
		selection.unselect_all()
		selection.select_path(row)
		self.treeview.scroll_to_cell(row)
		return True

	def setcoords(self):

		buffer = self.view.get_buffer()
		cursor = buffer.get_iter_at_mark(buffer.get_insert())
		rectangle  = self.view.get_iter_location(cursor)
		curx, cury = self.view.buffer_to_window_coords(gtk.TEXT_WINDOW_TEXT, rectangle.x, rectangle.y)
		curh = rectangle.height
		win = self.view.get_window(gtk.TEXT_WINDOW_TEXT)
		rectangle  = self.view.get_visible_rect()
		winx, winy = win.get_origin()
		winw, winh = rectangle.width, rectangle.height
        
		posx, posy = winx + curx, winy + cury + curh
		self.x = posx
		self.y = posy


	def getSuggestions(self, word):

		suggests = []
		for keyword in self.keywords:
			if(keyword.startswith(word)):
				suggests.append(keyword)
		return suggests

	def getWord(self):
		buffer = self.view.get_buffer()
		iter = buffer.get_iter_at_mark(buffer.get_insert())
		# print("iter:",iter)
		pos = iter.backward_search(' ',gtk.TEXT_SEARCH_TEXT_ONLY)
		# print(pos)
		if(pos == None):
			pos = iter.backward_search('\n',gtk.TEXT_SEARCH_TEXT_ONLY)
		if(pos == None):
			pos = [0,buffer.get_start_iter()]

		word = buffer.get_text(pos[1], iter)
		return word


	def addWord(self, suggestedWord):
		buffer = self.view.get_buffer()
		iter = buffer.get_iter_at_mark(buffer.get_insert())
		word = self.getWord()
		pos = iter.backward_search(word,gtk.TEXT_SEARCH_TEXT_ONLY)
		if(pos == None):
			buffer.insert(iter,suggestedWord)
		else:
			buffer.delete(pos[0],pos[1])
			buffer.insert(pos[0],suggestedWord)