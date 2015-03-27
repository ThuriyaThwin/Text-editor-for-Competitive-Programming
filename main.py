import ConfigParser
import gtk
import gobject
import os
import time
import subprocess
import re
import string
import urllib2
import bs4
import thread
import threading
import webbrowser
import gtksourceview2
from htmlparser import *
from pygoogle import pygoogle

#TODO
#redo
#more languages
#more websites
#better way to fix open close quotes in error message for googling
#background colors/ themes


class MainWindow():

	def __init__(self):

		#list of lists to hold values for each page in the notebook 
		# [scrolledwindow object, labelbox object, filepath, save state, undoStates, undoThreadOn]
		self.CodeNotebookPageVals = [] 
		
		#to hold list of keywords to highlight
		self.keywords = [] 

		#list to hold list of tags added to all the pages
		self.tags = [] 

		#dictionary to load/save preferences to
		self.PreferencesDict = {} 

		#index of the previous file to open (needs working)
		self.PreviousFileIndex = 0 

		#used to skip saving text state in case undo was performed(since performing undo will also call the function due to change in text)
		self.UndoPerformed = False 

		self.loadKeywords()
		self.loadPreferences()
		self.init()

	def init(self):

		self.mainWindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.mainWindow.set_title("Zarroc")
		self.mainWindow.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#696969'))
		self.mainWindow.set_position(gtk.WIN_POS_CENTER)
		self.mainWindow.set_default_size(500,500)
		#connect the close button
		self.mainWindow.connect('destroy' , lambda w: gtk.main_quit())
		#set the opacity of the window
		self.mainWindow.set_opacity(self.PreferencesDict["opacity"])
		#perform changes(setting the window separators) to the window when it resizes
		self.mainWindow.connect("configure_event",self.WindowResize)

		#main layout to hold child layouts
		self.mainVerticalLayout = gtk.VBox()
		self.mainWindow.add(self.mainVerticalLayout)

		#Create the menu bar
		self.CreateMenuBar()

		#Set hotkeys
		self.SetHotkeys()

		#Create Toolbar
		self.CreateToolBar()

		#Create URL Bar
		self.CreateUrlBar()

		#create the labels for IO
		self.CreateIOLabels()

		#Vertical Pannable Window that holds Input Output text boxes, CodeEditor box and Compiler box
		self.IOCodeWindow = gtk.VPaned()		
		#set the divider
		self.IOCodeWindow.set_position(100)

		#Create input/output text boxes
		self.CreateIOTextBoxes()

		#create the code editor text box
		self.CreateCodeEditorBox()

		#Center Window that contains 1 Vertical paned window and compiler output area
		self.CenterWindow = gtk.VPaned()
		self.mainVerticalLayout.pack_start(self.CenterWindow,padding = 5)
		self.CenterWindow.add(self.IOCodeWindow)

		#set compiler output area
		self.CreateConsoleBox()



		self.mainWindow.show_all()
		gtk.main()


	#function called when window is resized
	#used to set the separators of the paned windows
	def WindowResize(self,widget,allocation):

		#adjust pane bar between IO window
		self.IOPanedWindow.set_position(int(allocation.width*0.5))
		#adjust pane bar between IO window and code editor window
		self.IOCodeWindow.set_position(int(allocation.height*0.2))
		#adjust pane bar between IO,codeeditor and compiler output window
		self.CenterWindow.set_position(int(allocation.height*0.8))


	#Creates the compiler output window
	def CreateConsoleBox(self):

		#create a scrolled window for compiler/run output
		self.ConsoleScrolledWindow = gtk.ScrolledWindow()
		self.ConsoleScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.ConsoleText = gtk.TextView()
		self.ConsoleText.set_editable(False) #disable user to edit the content
		self.ConsoleScrolledWindow.add(self.ConsoleText)
		#add to center window(VPaned)
		self.CenterWindow.add(self.ConsoleScrolledWindow)

	def CreateCodeEditorBox(self):

		#Box to hold CodeNotebook
		self.CodeEditorBox = gtk.HBox()

		

		#code notebook to hold all files as tabs
		self.CodeNotebook = gtk.Notebook() 
		if(self.PreferencesDict["tab_position"] == "TOP"):
			self.CodeNotebook.set_tab_pos(gtk.POS_TOP)
		elif(self.PreferencesDict["tab_position"] == "BOTTOM"):
			self.CodeNotebook.set_tab_pos(gtk.POS_BOTTOM)
		elif(self.PreferencesDict["tab_position"] == "LEFT"):
			self.CodeNotebook.set_tab_pos(gtk.POS_LEFT)
		elif(self.PreferencesDict["tab_position"] == "RIGHT"):
			self.CodeNotebook.set_tab_pos(gtk.POS_RIGHT)
		self.CodeNotebook.set_show_tabs(True)
		self.CodeNotebook.set_show_border(True)
		self.CodeNotebook.set_scrollable(True)
		self.CodeNotebook.show()

		#create and add a notebook page
		page = self.CreateNotebookPage()
		self.CodeNotebookPageVals.append(page)
		self.CodeNotebook.append_page(page[0], page[1])

		#add notebook to box
		self.CodeEditorBox.pack_start(self.CodeNotebook,padding = 5)
		#adding the code editor scrolled window to vertical pannable window
		self.IOCodeWindow.add(self.CodeEditorBox)

	#creates a page for the codenotebook
	def CreateNotebookPage(self, file_path = '/Untitled', text = ''):

		#Hbox that makes up the tab label
		labelBox = gtk.HBox()
		pageLabel = gtk.Label(self.GetFileName(file_path)) #tab label
		pageLabel.show()		
		image = gtk.Image() #image of cross button
		image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
		closeButton = gtk.Button() #close image button
		closeButton.set_image(image) #set the image
		closeButton.set_relief(gtk.RELIEF_NONE) #set the relief of button to none
		closeButton.show()
		labelBox.pack_start(pageLabel)
		labelBox.pack_start(closeButton)
		labelBox.show()
		
		#code editor window (tab content)
		CodeEditorScrolledWindow = gtk.ScrolledWindow()
		CodeEditorScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		#code editor text object
		CodeEditorText = gtksourceview2.View()
		CodeEditorText.set_indent_width(4)
		CodeEditorText.set_highlight_current_line(True)
		CodeEditorText.set_insert_spaces_instead_of_tabs(True)
		CodeEditorText.set_show_line_numbers(True)
		CodeEditorText.set_show_line_marks(True)
		CodeEditorText.set_auto_indent(True)
		# CodeEditorText.set_show_right_margin(True)
		CodeEditorText.set_smart_home_end(True)
		buffer = CodeEditorText.get_buffer()
		buffer.set_text(text)
		# CodeEditorText.set_buffer(buffer)
		# buffer.connect('insert-text',self.TextChangedCodeEditor) #set callback function whenever text is changed
		CodeEditorText.connect('key_press_event',self.CodeEditorKeyPress)
		# buffer.connect('delete-range',self.TextChangedCodeEditor)
		CodeEditorText.show()
		CodeEditorScrolledWindow.add(CodeEditorText)
		CodeEditorScrolledWindow.show()

		#connect the close button
		closeButton.connect("clicked", self.ClosePage, CodeEditorScrolledWindow)

		#append a list to hold tags of the file
		self.tags.append([])

		if(file_path == '/Untitled'):
			# [scrolledwindow object, labelbox object, filepath, save state, undoStates, undoThreadOn]
			return [CodeEditorScrolledWindow, labelBox, None, True, [''], False] 
		else:
			return [CodeEditorScrolledWindow, labelBox, file_path, True, [''], False]
	

	#function to close the respective tab
	def ClosePage(self, widget, child):
		
		#get the index of the page that is being closed
		index = self.CodeNotebook.page_num(child)

		#ask to save if not saved
		if(not self.CodeNotebookPageVals[index][3]):
			if(not self.ConfirmSaveDialog(index)):
				return
		else:
			#remove and delete the page
			filepath = self.CodeNotebookPageVals[index][2]
			self.CodeNotebook.remove_page(index)
			del self.CodeNotebookPageVals[index]
			del self.tags[index]
			if(filepath != None):
				try:
					self.PreferencesDict['recent_files_list'].remove(filepath)
				except ValueError:
					pass
				self.PreferencesDict['recent_files_list'] = [filepath] + self.PreferencesDict['recent_files_list']
				self.PreferencesDict['recent_files_list'] = self.PreferencesDict['recent_files_list'][0:10]
				self.SavePreferences()
				self.SetRecentFilesMenu()
			self.PreviousFileIndex = 0

	#called when a key is pressed into the codeeditor
	def CodeEditorKeyPress(self, widget, event):

		#if the key pressed was backspace or delete or a printable string
		if( (event.keyval == 65288 or event.keyval == 65535 or event.string in string.printable) and (not event.string == '')) :
			self.TextChangedCodeEditor()

		
	# Once the thread is over reset the thread state to false to save the state if user types again
	def undoThreadOver(self, page_num):
		self.CodeNotebookPageVals[page_num][5] = False
		# print("thread over : ",self.CodeNotebookPageVals[page_num][4])

	#stores the current text state and waits a second to let the user type before storing another state for an undo move
	def undoThread(self,page_num):
		time.sleep(1)
		gobject.idle_add(self.undoThreadOver,page_num)
				

	#called when text is changed in the editor
	def TextChangedCodeEditor(self,arg1 = None, arg2 = None, arg3 = None, arg4 = None):
		page_num = self.CodeNotebook.get_current_page()
		#if undo was done then no need to save text state
		if(not self.UndoPerformed):
			#if the thread is already not running then start it
			if(not self.CodeNotebookPageVals[page_num][5]):
				
				buffer = self.CodeNotebookPageVals[page_num][0].get_children()[0].get_buffer()
				if(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter()) !=  self.CodeNotebookPageVals[page_num][4][-1]):
					self.CodeNotebookPageVals[page_num][4].append(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter()))
					self.CodeNotebookPageVals[page_num][5] = True
					threading.Thread(target = self.undoThread, args = (page_num,) ).start()
			else:
				# print("thread running")
				pass
		else:
			self.UndoPerformed = False
			# print("passing since undo done")
			pass
			# print(self.CodeNotebookPageVals)
		self.CodeNotebookPageVals[page_num][3] = False
		self.HighlightKeywords()
		

	#function to go throught the text in the editor box and highlight keywords
	#removes all tags and reapplies them everytime a key is pressed
	#TODO can be improved
	def HighlightKeywords(self):
		#HIGHLIGHT KEYWORDS BELOW
		page_num = self.CodeNotebook.get_current_page()
		#get buffer of page
		buffer = self.CodeNotebookPageVals[page_num][0].get_children()[0].get_buffer()

		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()

		#remove tags from buffer and tagtable
		try:
			for tag in self.tags[page_num]:
				buffer.remove_tag(tag,start_iter,end_iter)
				buffer.get_tag_table().remove(tag)
		except IndexError:
			self.tags.append([])

		#set tags list to empty list
		self.tags[page_num] = []

		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()

		#highlight keywords
		for word in self.keywords:
			#search from beginning
			start_iter = buffer.get_start_iter()
			pos = start_iter.forward_search(word,gtk.TEXT_SEARCH_TEXT_ONLY)		
			#if search found
			while(pos != None):
				#check if the word is not a substring but an actual word
				if(pos[1].ends_word() and pos[0].starts_word()):
					self.tags[page_num].append(buffer.create_tag(None,foreground = '#ff0000'))
					buffer.apply_tag(self.tags[page_num][-1], pos[0], pos[1])
				#set iter to end position
				start_iter = pos[1]
				#search again
				pos = start_iter.forward_search(word,gtk.TEXT_SEARCH_TEXT_ONLY)		


	#input output text box codes below

	def CreateIOLabels(self):

		#Labels Bar for Input Output
		self.IOLabelBox = gtk.HBox()
		self.mainVerticalLayout.pack_start(self.IOLabelBox,fill = False, expand = False)
		#Input Label
		self.InputLabel = gtk.Label("Input")
		self.IOLabelBox.pack_start(self.InputLabel)
		#Output Label
		self.OutputLabel = gtk.Label("Output")
		self.IOLabelBox.pack_start(self.OutputLabel)

	def CreateIOTextBoxes(self):

		#Input Output Layout Box
		self.IOBox = gtk.HBox()
		self.IOCodeWindow.add(self.IOBox)

		#Input TextView inside a scrollable window
		self.InputScrolledWindow = gtk.ScrolledWindow()
		self.InputScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.InputText = gtk.TextView()
		self.InputScrolledWindow.add(self.InputText)

		#OutputTextView inside a scrollable window
		self.OutputScrolledWindow = gtk.ScrolledWindow()
		self.OutputScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.OutputText = gtk.TextView()
		self.OutputScrolledWindow.add(self.OutputText)

		#Horizontally Paned Window
		self.IOPanedWindow = gtk.HPaned()
		self.IOPanedWindow.add(self.InputScrolledWindow)
		self.IOPanedWindow.add(self.OutputScrolledWindow)

		#TODO need to create a function that auto sets the position when window size changes
		self.IOPanedWindow.set_position(100)

		#adding the panned window to IOBox
		self.IOBox.pack_start(self.IOPanedWindow,padding = 5)


	#Url bar functions below

	#add the url bar to the window
	def CreateUrlBar(self):

		#TopFrame containing URL bar
		self.UrlBox = gtk.HBox()
		self.mainVerticalLayout.pack_start(self.UrlBox, fill = False, expand = False)
		#URL label
		self.UrlLabel = gtk.Label('URL :')
		self.UrlBox.pack_start(self.UrlLabel, fill = False, expand = False, padding = 5)
		#URL entry box
		self.UrlTextView = gtk.TextView()
		self.UrlTextView.connect('key_release_event',self.urlBarKeyPressed)
		self.UrlTextView.set_events(gtk.gdk.KEY_RELEASE_MASK)
		self.UrlBox.pack_start(self.UrlTextView,padding = 5)

		self.UrlButton = gtk.Button("GO")
		self.UrlButton.connect('clicked',self.urlFetchThread)
		self.UrlBox.pack_start(self.UrlButton,False,False,padding = 5)


	#fetch test cases from url and add to input output boxes
	def getTestCases(self, io):
		print("getting test cases")

		inputbuffer = self.InputText.get_buffer()
		inputbuffer.set_text('')

		outputbuffer = self.OutputText.get_buffer()
		outputbuffer.set_text('')

		inputbuffer.set_text(io[0])
		self.InputText.set_buffer(inputbuffer)
		outputbuffer.set_text(io[1])
		self.OutputText.set_buffer(outputbuffer)


	def urlFetcher(self):
		inputbuffer = self.InputText.get_buffer()
		inputbuffer.set_text('fetching test case...')

		outputbuffer = self.OutputText.get_buffer()
		outputbuffer.set_text('fetching test case...')

		buffer = self.UrlTextView.get_buffer()
		urlVal = buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter())
		io = getInputOutput(urlVal)
		gobject.idle_add(self.getTestCases,io)


	#called when Enter is pressed on the URL bar or Go button is clicked
	def urlFetchThread(self,widget = None,event = None):
		threading.Thread(target = self.urlFetcher, args = () ).start()

	#called when enter is pressed into the URL bar
	def urlBarKeyPressed(self, widget, event):
		if(event.keyval == 65293):
			self.urlFetchThread()

	#MENU BAR FUNCTIONS BELOW

	def CreateMenuBar(self):

		self.CreateFileMenuOption()
		self.CreateEditMenuOption()
		self.CreateViewMenuOption()

		#create menu bar
		self.MenuBar = gtk.MenuBar()
		self.mainVerticalLayout.pack_start(self.MenuBar, fill = False, expand = False)
		self.MenuBar.show()
		
		#add file options to menu bar		
		self.MenuBar.append(self.FileOption)
		self.MenuBar.append(self.EditOption)
		self.MenuBar.append(self.ViewOption)

	#Create file menu options
	def CreateFileMenuOption(self):
		
		self.FileMenu = gtk.Menu()
		self.NewEmptyFile = gtk.MenuItem("New")
		self.OpenFile = gtk.MenuItem("Open")
		self.RecentFiles = gtk.MenuItem("Recent Files")
		separator1 = gtk.SeparatorMenuItem()
		self.SaveFile = gtk.MenuItem("Save")
		self.SaveAsFile = gtk.MenuItem("Save As")
		separator2 = gtk.SeparatorMenuItem()
		self.CloseFile = gtk.MenuItem("Close")
		self.Quit = gtk.MenuItem("Quit")
		#append to menu
		self.FileMenu.append(self.NewEmptyFile)
		self.FileMenu.append(self.OpenFile)
		self.FileMenu.append(self.RecentFiles)
		self.FileMenu.append(separator1)
		self.FileMenu.append(self.SaveFile)
		self.FileMenu.append(self.SaveAsFile)
		self.FileMenu.append(separator2)
		self.FileMenu.append(self.CloseFile)
		self.FileMenu.append(self.Quit)
		#connect click functions
		self.NewEmptyFile.connect("activate", self.OpenNewEmptyFile)
		self.OpenFile.connect("activate", self.OpenFileDialog)
		self.CloseFile.connect("activate", self.CloseCurrentPage)
		self.SaveFile.connect("activate", self.SaveFileDialog)
		self.SaveAsFile.connect("activate", self.SaveAsFileDialog)
		self.Quit.connect("activate", self.QuitApp)
		#show options
		self.NewEmptyFile.show()
		self.OpenFile.show()
		self.CloseFile.show()
		self.RecentFiles.show()
		self.SaveFile.show()
		self.SaveAsFile.show()
		self.Quit.show()
		
		#create the reopen last file menu item
		# self.ReopenLastFileItem = gtk.MenuItem("Reopen Last")
		# self.ReopenLastFileItem.connect("activate", self.ReopenLastFile)
		# self.ReopenLastFileItem.show()
		#set the recent files menu
		self.SetRecentFilesMenu()		

		#menu item file
		self.FileOption = gtk.MenuItem("File")
		self.FileOption.show()
		self.FileOption.set_submenu(self.FileMenu)
	
	#creates the recent files menu
	#also called when a tab is closed to refresh recent files list
	def SetRecentFilesMenu(self):

		self.RecentFilesMenu = gtk.Menu()
		self.ReopenLastFileItem = gtk.MenuItem("Reopen Last")
		self.ReopenLastFileItem.connect("activate", self.ReopenLastFile)
		try:
			self.ReopenLastFileItem.add_accelerator("activate", self.accel_group, ord('T'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, gtk.ACCEL_VISIBLE) 
		except AttributeError:
			pass
		self.ReopenLastFileItem.show()
		self.RecentFilesMenu.append(self.ReopenLastFileItem)
		# self.ReopenLastFileItem.show()

		separator = gtk.SeparatorMenuItem()
		self.RecentFilesMenu.append(separator)
		# print("recent_files_list", self.PreferencesDict['recent_files_list'])
		for tempFile in self.PreferencesDict['recent_files_list']:
			fileItem = gtk.MenuItem(self.GetFileName(tempFile))
			self.RecentFilesMenu.append(fileItem)
			fileItem.connect("activate",self.OpenRecentFile, self.GetFileName(tempFile))
			fileItem.show()
		self.RecentFiles.set_submenu(self.RecentFilesMenu)


	#Create Edit Menu
	def CreateEditMenuOption(self):

		self.EditMenu = gtk.Menu()
		self.Undo = gtk.MenuItem("Undo")
		separator1 = gtk.SeparatorMenuItem()
		self.Cut = gtk.MenuItem("Cut")
		self.Copy = gtk.MenuItem("Copy")
		self.Paste = gtk.MenuItem("Paste")
		separator2 = gtk.SeparatorMenuItem()
		self.Preferences = gtk.MenuItem("Preferences")
		self.EditMenu.append(self.Undo)
		self.EditMenu.append(separator1)
		self.EditMenu.append(self.Cut)
		self.EditMenu.append(self.Copy)
		self.EditMenu.append(self.Paste)
		self.EditMenu.append(separator2)
		self.EditMenu.append(self.Preferences)
		self.Undo.connect("activate",self.UndoText)
		self.Cut.connect("activate",self.CutText)
		self.Copy.connect("activate",self.CopyText)
		self.Paste.connect("activate",self.PasteText)
		self.Preferences.connect("activate",self.OpenPreferences)
		self.Cut.show()
		self.Preferences.show()

		#menu edit item
		self.EditOption = gtk.MenuItem("Edit")
		self.EditOption.show()
		self.EditOption.set_submenu(self.EditMenu)

	def CreateViewMenuOption(self):

		self.ViewMenu = gtk.Menu()
		#show input outbox check item
		self.ShowInputOutputPane = gtk.CheckMenuItem("Show Input/Output Window")
		self.ShowInputOutputPane.set_active(True)
		self.ShowInputOutputPane.connect("toggled",self.ToggleInputOutputWindow)
		self.ViewMenu.append(self.ShowInputOutputPane)
		self.ShowInputOutputPane.show()

		#show console check item
		self.ShowConsoleWindow  = gtk.CheckMenuItem("Show Console Window")
		self.ShowConsoleWindow.set_active(True)
		self.ShowConsoleWindow.connect("toggled",self.ToggleConsoleWindow)
		self.ViewMenu.append(self.ShowConsoleWindow)
		self.ShowConsoleWindow.show()

		#show url bar
		self.ShowUrlBar  = gtk.CheckMenuItem("Show Url Bar")
		self.ShowUrlBar.set_active(True)
		self.ShowUrlBar.connect("toggled",self.ToggleUrlBar)
		self.ViewMenu.append(self.ShowUrlBar)
		self.ShowUrlBar.show()

		self.ViewOption = gtk.MenuItem("View")
		self.ViewOption.show()
		self.ViewOption.set_submenu(self.ViewMenu)

	#reopen the previous file (hotkey function)
	def ReopenLastFile(self, widget):
		
		filepath = self.PreferencesDict['recent_files_list'][self.PreviousFileIndex]
		self.OpenRecentFile(None, filepath)
		self.PreviousFileIndex += 1


	#show hide url bar
	def ToggleUrlBar(self, widget):

		if(self.ShowUrlBar.get_active()):
			self.UrlBox.show()
		else:
			self.UrlBox.hide()

	#show hide console window
	def ToggleConsoleWindow(self, widget):

		if(self.ShowConsoleWindow.get_active()):
			self.ConsoleScrolledWindow.show()
		else:
			self.ConsoleScrolledWindow.hide()
		
	#show hide input output pane/window
	def ToggleInputOutputWindow(self, widget):

		if(self.ShowInputOutputPane.get_active()):
			self.IOLabelBox.show()
			self.IOBox.show()
		else:
			self.IOLabelBox.hide()
			self.IOBox.hide()

	#opens the recent file
	def OpenRecentFile(self,widget,filepath):

		filename = self.GetFileName(filepath)
		f = open(filepath)
		text = f.read()
		f.close()
		page = self.CreateNotebookPage(filename, text)
		self.CodeNotebookPageVals.append(page)
		self.CodeNotebook.append_page(page[0], page[1])		
		self.CodeNotebook.set_current_page(-1)
		self.HighlightKeywords()


	#close the current page
	def CloseCurrentPage(self, widget):

		index = self.CodeNotebook.get_current_page()
		# print(self.CodeNotebookPageVals)
		if(not self.CodeNotebookPageVals[index][3]):
			if(not self.ConfirmSaveDialog(index)):
				return
		else:
			filepath = self.CodeNotebookPageVals[index][2]
			self.CodeNotebook.remove_page(index)
			del self.tags[index]
			if(filepath != None):
				try:
					self.PreferencesDict['recent_files_list'].remove(filepath)
				except ValueError:
					pass
				self.PreferencesDict['recent_files_list'] = [filepath] + self.PreferencesDict['recent_files_list']
				self.PreferencesDict['recent_files_list'] = self.PreferencesDict['recent_files_list'][0:10]
				self.SavePreferences()
				self.SetRecentFilesMenu()
			self.PreviousFileIndex = 0

	#function to undo text
	def UndoText(self,widget):

		page_num = self.CodeNotebook.get_current_page()
		self.UndoPerformed = True
		buffer = self.CodeNotebookPageVals[page_num][0].get_children()[0].get_buffer()
		text = self.CodeNotebookPageVals[page_num][4][-1]
		buffer.set_text(text)
		del self.CodeNotebookPageVals[page_num][4][len(self.CodeNotebookPageVals[page_num][4])-1]
		if(len(self.CodeNotebookPageVals[page_num][4]) == 0):
			self.CodeNotebookPageVals[page_num][4].append('')
		# print("undo performed :",self.CodeNotebookPageVals[page_num][4])
		self.HighlightKeywords()


	#function to paste text into the editor from clipboard
	def PasteText(self,widget):
		
		child = self.mainWindow.get_focus()
		#don't allow pasting in the console output box
		if(child == self.ConsoleText):
			return
		buffer = child.get_buffer()
		clipboard =  gtk.Clipboard()
		buffer.paste_clipboard(clipboard, None, True)

	#function to copy selected text onto the clipboard
	def CopyText(self,widget):
		
		child = self.mainWindow.get_focus()
		buffer = child.get_buffer()
		clipboard =  gtk.Clipboard()
		buffer.copy_clipboard(clipboard)

	#function to cut selected text onto the clipboard
	def CutText(self,widget):
		
		child = self.mainWindow.get_focus()
		#don't allow cutting in the console output box
		if(child == self.ConsoleText):
			return
		buffer = child.get_buffer()
		clipboard = gtk.Clipboard()
		buffer.cut_clipboard(clipboard,True)

	#Response on clicking preferences in edit menu
	def OpenPreferences(self, widget):

		#create dialog
		self.PreferencesDialog = gtk.Dialog("Preferences")
		self.PreferencesDialog.set_has_separator(True)
		
		#Hbox to hold label and opacity entry
		hbox = gtk.HBox()
		label = gtk.Label("Opacity (0-1) :")
		label.show()
		hbox.pack_start(label)
		#opacity entry box
		self.PreferencesOpacityEntry = gtk.Entry()
		self.PreferencesOpacityEntry.set_text(str(self.PreferencesDict['opacity']))
		self.PreferencesOpacityEntry.connect('changed', self.checkOpacityEntry) #connect to function to validate values
		self.PreferencesOpacityEntry.show()
		hbox.pack_start(self.PreferencesOpacityEntry)
		hbox.show()
		self.PreferencesDialog.vbox.pack_start(hbox,padding = 5)
		
		#create radio buttons for tab position
		hbox = gtk.HBox()
		label = gtk.Label("Tab Position : ")
		label.show()
		hbox.pack_start(label)
		vbox = gtk.VBox()
		tabsTopRadio = gtk.RadioButton(None,"Top")
		tabsTopRadio.connect("toggled",self.changeCodeNotebookTabPosition,"TOP")
		#set to marked if set by user
		if(self.PreferencesDict["tab_position"] == "TOP"):
			tabsTopRadio.set_active(True)
		tabsTopRadio.show()

		vbox.pack_start(tabsTopRadio)
		tabsLeftRadio = gtk.RadioButton(tabsTopRadio,"Left")
		tabsLeftRadio.connect("toggled",self.changeCodeNotebookTabPosition,"LEFT")
		if(self.PreferencesDict["tab_position"] == "LEFT"):
			tabsLeftRadio.set_active(True)
		tabsLeftRadio.show()

		vbox.pack_start(tabsLeftRadio)
		tabsRightRadio = gtk.RadioButton(tabsTopRadio,"Right")
		tabsRightRadio.connect("toggled",self.changeCodeNotebookTabPosition,"RIGHT")
		if(self.PreferencesDict["tab_position"] == "RIGHT"):
			tabsRightRadio.set_active(True)
		tabsRightRadio.show()

		vbox.pack_start(tabsRightRadio)
		tabsBottomRadio = gtk.RadioButton(tabsTopRadio,"Bottom")
		tabsBottomRadio.connect("toggled",self.changeCodeNotebookTabPosition,"BOTTOM")
		if(self.PreferencesDict["tab_position"] == "BOTTOM"):
			tabsBottomRadio.set_active(True)
		tabsBottomRadio.show()

		vbox.pack_start(tabsBottomRadio)
		hbox.show()
		vbox.show()
		hbox.pack_start(vbox)
		self.PreferencesDialog.vbox.pack_start(hbox,padding = 5)

		#add cancel button
		button = self.PreferencesDialog.add_button("Close",gtk.RESPONSE_ACCEPT)
		button.connect("clicked",self.ClosePreferences) #close the box on clicking cancel
		button.show()

		self.PreferencesDialog.run()
		self.PreferencesDialog.destroy()	

	#changes the position of the tab to the value of option
	def changeCodeNotebookTabPosition(self,widget,option):

		if(option == "BOTTOM"):
			self.CodeNotebook.set_tab_pos(gtk.POS_BOTTOM)
			self.PreferencesDict["tab_position"] = "BOTTOM"
		elif(option == "TOP"):
			self.CodeNotebook.set_tab_pos(gtk.POS_TOP)
			self.PreferencesDict["tab_position"] = "TOP"
		elif(option == "RIGHT"):
			self.CodeNotebook.set_tab_pos(gtk.POS_RIGHT)
			self.PreferencesDict["tab_position"] = "RIGHT"
		elif(option == "LEFT"):
			self.CodeNotebook.set_tab_pos(gtk.POS_LEFT)
			self.PreferencesDict["tab_position"] = "LEFT"
		self.SavePreferences();

	#check if value inside entry box is numeric
	def checkOpacityEntry(self, widget):

		try:
			val = float(self.PreferencesOpacityEntry.get_text())
			if(val<0):
				self.PreferencesOpacityEntry.set_text('0')
			elif(val>1):
				self.PreferencesOpacityEntry.set_text('1')
		except ValueError:
			self.PreferencesOpacityEntry.set_text('')
		try:
			val = float(self.PreferencesOpacityEntry.get_text())
		except ValueError:
			val = 1
		self.mainWindow.set_opacity(val)
		self.PreferencesDict["opacity"] = val
		self.SavePreferences()

	#write preferences to preferences file
	def SavePreferences(self):

		config = ConfigParser.RawConfigParser()
		config.add_section('Section1')
		config.set('Section1','opacity',self.PreferencesDict['opacity'])
		config.set('Section1','tab_position',self.PreferencesDict['tab_position'])
		config.set('Section1','recent_files_list',self.PreferencesDict['recent_files_list'])
		with open('preferences.cfg', 'w') as configfile:
			config.write(configfile)

	#load the stored preferences
	def loadPreferences(self):

		config = ConfigParser.RawConfigParser()
		config.read('preferences.cfg')
		try:
			self.PreferencesDict["opacity"] = eval(config.get('Section1', 'opacity'))
		except:
			self.PreferencesDict["opacity"] = 1
		try:
			self.PreferencesDict["tab_position"] = config.get('Section1', 'tab_position')
		except:
			self.PreferencesDict["tab_position"] = "TOP"
		try:
			self.PreferencesDict["recent_files_list"] = eval(config.get('Section1','recent_files_list'))
		except:
			self.PreferencesDict["recent_files_list"] = []

	#close the dialog box
	def ClosePreferences(self,widget):

		self.PreferencesDialog.destroy()
		
	#open an empty file and append it to the end of the notebook tabs
	def OpenNewEmptyFile(self,widget):

		page = self.CreateNotebookPage()
		self.CodeNotebook.append_page(page[0],page[1])
		self.CodeNotebookPageVals.append(page)
		self.CodeNotebook.set_current_page(-1)


	def ConfirmSaveDialog(self, index):

		#TODO
		dialogWindow = gtk.Dialog("Preferences", None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
										 (gtk.STOCK_NO, gtk.RESPONSE_NO, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		dialogWindow.set_has_separator(True)
		dialogWindow.set_default_response(gtk.RESPONSE_YES)
		hbox = gtk.HBox()
		label = gtk.Label("Save before Quitting?")
		label.show()
		hbox.show()
		hbox.pack_start(label)
		dialogWindow.vbox.pack_start(hbox, padding = 5)

		response = dialogWindow.run()

		if(response == gtk.RESPONSE_NO):
			print("close without save")
			filepath = self.CodeNotebookPageVals[index][2]
			self.CodeNotebook.remove_page(index)
			del self.CodeNotebookPageVals[index]
			del self.tags[index]
			if(filepath != None):
				try:
					self.PreferencesDict['recent_files_list'].remove(filepath)
				except ValueError:
					pass
				self.PreferencesDict['recent_files_list'] = [filepath] + self.PreferencesDict['recent_files_list']
				self.PreferencesDict['recent_files_list'] = self.PreferencesDict['recent_files_list'][0:10]
				self.SavePreferences()
				self.SetRecentFilesMenu()
			self.PreviousFileIndex = 0
		elif(response == gtk.RESPONSE_CANCEL):
			print("Dont close")
		elif(response == gtk.RESPONSE_OK):
			print("save file")
			self.SaveFileDialog(None, page_num = index)
			filepath = self.CodeNotebookPageVals[index][2]
			self.CodeNotebook.remove_page(index)
			del self.CodeNotebookPageVals[index]
			del self.tags[index]
			if(filepath != None):
				try:
					self.PreferencesDict['recent_files_list'].remove(filepath)
				except ValueError:
					pass
				self.PreferencesDict['recent_files_list'] = [filepath] + self.PreferencesDict['recent_files_list']
				self.PreferencesDict['recent_files_list'] = self.PreferencesDict['recent_files_list'][0:10]
				self.SavePreferences()
				self.SetRecentFilesMenu()
			self.PreviousFileIndex = 0
		dialogWindow.destroy()


	#create the open file dialog and open the selected file in a new tab if any
	def OpenFileDialog(self, widget):

		dialog = gtk.FileChooserDialog("Open..", None, gtk.FILE_CHOOSER_ACTION_OPEN, 
											(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		response = dialog.run()
		if response == gtk.RESPONSE_OK:

			filestream = open(dialog.get_filename()) #open stream to read file
			filepath = dialog.get_filename() #extract filename
			text = filestream.read() #extract text from file stream
			filestream.close() #close stream

			#create the page and add the text to the page
			page = self.CreateNotebookPage(filepath, text)
			#append page details to notebook list
			self.CodeNotebookPageVals.append(page)
			#append the page into the code notebook(set of tabs)
			self.CodeNotebook.append_page(page[0], page[1])		

		elif response == gtk.RESPONSE_CANCEL:
			print('Closed, no files selected') #log
		dialog.destroy()
		self.CodeNotebook.set_current_page(-1)
		self.HighlightKeywords()


	#open the save as file dialog and save the file 
	def SaveAsFileDialog(self, widget):

		dialog = gtk.FileChooserDialog("Save As..", None, gtk.FILE_CHOOSER_ACTION_SAVE,
											(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		response = dialog.run()
		if response == gtk.RESPONSE_OK:

		    filestream = open(dialog.get_filename(),'w')
		    filepath = dialog.get_filename()

		    page_num = self.CodeNotebook.get_current_page()
		    buffer = self.CodeNotebookPageVals[page_num][0].get_children()[0].get_buffer()

		    filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
		    filestream.close()

		    self.CodeNotebookPageVals[page_num][1].get_children()[0].set_label(self.GetFileName(filepath))
		    self.CodeNotebookPageVals[page_num][2] = filepath

		elif response == gtk.RESPONSE_CANCEL:
		    print('Closed, no files selected') #log

		dialog.destroy()

	#close the app
	def QuitApp(self,widget):

		gtk.main_quit()

	#save the file if not saved already
	def SaveFileDialog(self, widget, page_num = None):
		print("savefiledialog")
		if(page_num == None):
			page_num = self.CodeNotebook.get_current_page()
		print(self.CodeNotebookPageVals[page_num])
		filepath =  self.CodeNotebookPageVals[page_num][2]
		print("filepaht :",filepath)
		if(filepath == None):
			dialog = gtk.FileChooserDialog("Save As..", None, gtk.FILE_CHOOSER_ACTION_SAVE,
											(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
			dialog.set_default_response(gtk.RESPONSE_OK)
			response = dialog.run()
			if response == gtk.RESPONSE_OK:
				filestream = open(dialog.get_filename(),'w')
				filepath = dialog.get_filename()
				self.CodeNotebookPageVals[page_num][2] = filepath
				page_num = self.CodeNotebook.get_current_page()
				# print("\ncurrent page : "+str(page_num)+'\n')
				buffer = self.CodeNotebookPageVals[page_num][0].get_children()[0].get_buffer()

				filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
				filestream.close()

				self.CodeNotebookPageVals[page_num][1].get_children()[0].set_label(self.GetFileName(filepath))
			elif response == gtk.RESPONSE_CANCEL:
				print('Closed, no files selected') #log
			dialog.destroy()
		else:
			filestream = open(filepath,'w')
			
			page_num = self.CodeNotebook.get_current_page()
			buffer = self.CodeNotebookPageVals[page_num][0].get_children()[0].get_buffer()
			
			filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
			filestream.close()

			self.CodeNotebookPageVals[page_num][1].get_children()[0].set_label(self.GetFileName(filepath))


	# setting hotkeys
	def SetHotkeys(self):

		self.accel_group = gtk.AccelGroup()
		self.mainWindow.add_accel_group(self.accel_group)
		self.OpenFile.add_accelerator("activate", self.accel_group, ord('O'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.SaveFile.add_accelerator("activate", self.accel_group, ord('S'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.CloseFile.add_accelerator("activate", self.accel_group, ord('W'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Quit.add_accelerator("activate", self.accel_group, ord('Q'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.NewEmptyFile.add_accelerator("activate", self.accel_group, ord('N'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Undo.add_accelerator("activate", self.accel_group, ord('Z'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Cut.add_accelerator("activate", self.accel_group, ord('X'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Copy.add_accelerator("activate", self.accel_group, ord('C'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Paste.add_accelerator("activate", self.accel_group, ord('V'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.ReopenLastFileItem.add_accelerator("activate", self.accel_group, ord('T'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, gtk.ACCEL_VISIBLE) 


	#TOOLBAR FUNCTIONS BELOW

	#creates and adds the toolbar to the window
	def CreateToolBar(self):

		#Toolbar box
		self.ToolBarBox = gtk.HBox()
		self.mainVerticalLayout.pack_start(self.ToolBarBox, fill = False, expand = False)
		#Compile and run button
		image = gtk.Image() 
		image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
		self.CompileRunButton = gtk.Button()
		self.CompileRunButton.set_image(image)
		self.CompileRunButton.connect('clicked',self.CompileRunCode)
		self.ToolBarBox.pack_start(self.CompileRunButton, fill = False, expand = False)

		self.SearchGoogle = gtk.Button("Google Errors")		
		self.SearchGoogle.connect('clicked',self.ShowGoogleResults)
		self.ToolBarBox.pack_start(self.SearchGoogle, fill = False, expand = False)		

	#function called when compile&run button is click
	def CompileRunCode(self,widget):

		#write code to file
		codefile = open('tempcode.cpp','w')
		page_num = self.CodeNotebook.get_current_page()
		buffer = self.CodeNotebookPageVals[page_num][0].get_children()[0].get_buffer()
		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()
		text = buffer.get_text(start_iter,end_iter,True)
		codefile.write(text)
		codefile.close()

		#clear console window
		buffer = self.ConsoleText.get_buffer()
		buffer.set_text('')


		#set label to compiling
		

		#perform compilation
		stream = subprocess.Popen(['g++','tempcode.cpp'],stdout = subprocess.PIPE,stdin = subprocess.PIPE,stderr= subprocess.PIPE)

		#get output/err
		output,err = stream.communicate()

		#if no output and no error => compilation successful
		if(output == '' and err == ''):

			print("compilation successfull") #log
			buffer = self.ConsoleText.get_buffer()
			buffer.insert(buffer.get_end_iter(), "Compilation Successful\n*******\n")

			#set label to compiled
			

			#set label to running
			

			#run the code
			stream = subprocess.Popen(['./a.out'], stdout = subprocess.PIPE, stdin = subprocess.PIPE,stderr = subprocess.PIPE)
			#get output and error
			buffer = self.InputText.get_buffer()
			inputvalue = buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter())
			print(inputvalue)
			output, err = stream.communicate(inputvalue)
			
			#if no error => run successful
			if(err == ''):

				print("run successfull") #log
				buffer = self.ConsoleText.get_buffer()
				buffer.insert(buffer.get_end_iter(), "Run Successful\n*******\n")

				#store user's output and required output
				userOutput = output.rstrip()

				buffer = self.OutputText.get_buffer()
				reqOutput = (buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())).rstrip()# self.outputText.get("1.0",END).rstrip()

				print("USEROUTPUT:") #log
				print(userOutput) #log

				print("REQOUTPUT:") #log 
				print(reqOutput) #log

				#compare both outputs and set label accordingly
				if(userOutput == reqOutput):
					print("output correct") #log
					buffer = self.ConsoleText.get_buffer()
					buffer.insert(buffer.get_end_iter(), userOutput+"\n*******\noutput Correct(matches)")
				else:
					print("output incorrect") #log
					buffer = self.ConsoleText.get_buffer()
					buffer.insert(buffer.get_end_iter(), userOutput+"\n*******\noutput Incorrect (does not match)")


			else: #show runtime error
				print("runtime error")
				print(err) #log
				buffer = self.ConsoleText.get_buffer()
				buffer.insert(buffer.get_end_iter(), "RUNTIME ERROR : \n"+err)
			
			#remove the temporary code file and run file
			stream = subprocess.Popen(['rm','a.out'])
			stream = subprocess.Popen(['rm','tempcode.cpp'])	
				
		else: #show compilation error
			print("compilation error") #log
			print(err) #log

			# buffer = gtk.TextBuffer()
			# buffer.set_text("COMPILATION ERROR : \n"+err)
			# self.ConsoleText.set_buffer(buffer)
			buffer = self.ConsoleText.get_buffer()
			buffer.insert(buffer.get_end_iter(), "COMPILATION ERROR : \n"+err)

	#google the error and create a dialog showing the results
	def ShowGoogleResults(self,widget):
		
		buffer = self.ConsoleText.get_buffer()
		err = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
		# print(err)

		if(err == None or err == ''):
			print('nothing to search') #log
			buffer.set_text('no errors to search')
			return

		start = err.find('error:')
		#if no error found then return
		if(start == -1):
			buffer.set_text('no errors to search')
			return
		start += 6
		stop = err[start:].find('\n')
		message = err[start:][:stop]

		# Remove open and close quotes from text
		# search better way to remove this
		if(message.find('\xe2') >= 0):
			message = message[:message.find('\xe2')] + message[message.find('\xe2')+1:]
		if(message.find('\xe2') >= 0):
			message = message[:message.find('\xe2')] + message[message.find('\xe2')+1:]
		if(message.find('\x80') >= 0):
			message = message[:message.find('\x80')] + message[message.find('\x80')+1:]
		if(message.find('\x80') >= 0):
			message = message[:message.find('\x80')] + message[message.find('\x80')+1:]
		if(message.find('\x98') >= 0):
			message = message[:message.find('\x98')] + message[message.find('\x98')+1:]
		if(message.find('\x99') >= 0):
			message = message[:message.find('\x99')] + message[message.find('\x99')+1:]
		print("search query : ", message) #log
		results = pygoogle(message)

		url_list = results.get_urls()
		print(url_list) #log

		self.GoogleResultsDialog = gtk.Dialog("Google search results")
		self.GoogleResultsDialog.set_default_size(300,300)
		self.GoogleResultsDialog.set_has_separator(True)
		
		print("Total results  : ",str(len(url_list))) #log
		#Hbox to hold label and opacity entry
		for i in range(0,min(10,len(url_list))):
			vbox = gtk.VBox()
			title = gtk.Label(self.GetTitleUrl(url_list[i]))
			title.show()
			vbox.pack_start(title)
			label_text = "<span foreground = 'blue' underline = 'low'> "+url_list[i]+" </span>"
			label = gtk.Label(label_text)
			label.set_use_markup(True)
			label.set_justify(gtk.JUSTIFY_LEFT)
			label.show()
			button = gtk.Button()
			button.add(label)
			button.set_relief(gtk.RELIEF_NONE)
			button.connect("clicked",self.OpenUrl,url_list[i])
			button.show()
			vbox.pack_start(button)
			vbox.show()
			self.GoogleResultsDialog.vbox.pack_start(vbox,padding = 5)

		self.GoogleResultsDialog.run()
		self.GoogleResultsDialog.destroy()


	#returns the title of the url received from the google search for errors
	def GetTitleUrl(self,url):

		try:
			response = urllib2.urlopen(url)
			source = response.read()
			soup = bs4.BeautifulSoup(source)
			return (soup.title.string)
		except:
			print("error in getting title")#log
			return("<Page Title>")

	def OpenUrl(self,widget,url):

		webbrowser.open_new_tab(url)

	#return the filename after extracting it from the filepath
	def GetFileName(self,filepath):
		return filepath[filepath.rfind('/')+1:]

	#loads keywords (currently only cpp)
	def loadKeywords(self):

		f = open('cppkeywords.txt','r')
		self.keywords = f.readlines()
		for i in range(0,len(self.keywords)):
			self.keywords[i] = self.keywords[i].rstrip()

if __name__ == "__main__":
	gtk.gdk.threads_init()
	window = MainWindow()