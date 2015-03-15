import gtk
import os
import subprocess
import re
import string
from htmlparser import *

keywords = []
tags = []

#TODO
#undo redo
#recent files
#more languages
#more websites
#global tags to class member

class MainWindow():

	def __init__(self):

		self.CodeNotebookPages = []
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
		self.mainWindow.set_opacity(0.8)
		#perform changes(setting the window separators) to the window when it resizes
		self.mainWindow.connect("configure_event",self.WindowResize)

		#main layout to hold child layouts
		self.mainVerticalLayout = gtk.VBox()
		self.mainWindow.add(self.mainVerticalLayout)

		#Crete the menu bar
		self.CreateMenuBar()

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
		self.CreateCompilerBox()

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
	def CreateCompilerBox(self):

		#create a scrolled window for compiler/run output
		self.CompilerScrolledWindow = gtk.ScrolledWindow()
		self.CompilerScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.CompilerText = gtk.TextView()
		self.CompilerText.set_editable(False) #disable user to edit the content
		self.CompilerScrolledWindow.add(self.CompilerText)
		#add to center window(VPaned)
		self.CenterWindow.add(self.CompilerScrolledWindow)

	def CreateCodeEditorBox(self):

		#Box to hold CodeNotebook
		self.CodeEditorBox = gtk.HBox()

		#code notebook to hold all files as tabs
		self.CodeNotebook = gtk.Notebook()
		self.CodeNotebook.set_tab_pos(gtk.POS_TOP)
		self.CodeNotebook.set_show_tabs(True)
		self.CodeNotebook.set_show_border(True)
		self.CodeNotebook.set_scrollable(True)
		self.CodeNotebook.show()

		
		page = self.CreateNotebookPage()
		self.CodeNotebookPages.append(page)
		self.CodeNotebook.append_page(page[0], page[1])

		#add notebook to box
		self.CodeEditorBox.pack_start(self.CodeNotebook,padding = 5)
		#adding the code editor scrolled window to vertical pannable window
		self.IOCodeWindow.add(self.CodeEditorBox)

	#creates a page for the codenotebook
	def CreateNotebookPage(self, label_name = 'Untitled', text = ''):

		#Hbox that makes up the tab label
		labelBox = gtk.HBox()
		pageLabel = gtk.Label(label_name) #tab label
		pageLabel.show()		
		image = gtk.Image() #image of cross button
		image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
		closeButton = gtk.Button() #close image button
		closeButton.set_image(image)
		closeButton.set_relief(gtk.RELIEF_NONE)
		closeButton.show()
		labelBox.pack_start(pageLabel)
		labelBox.pack_start(closeButton)
		labelBox.show()
		
		#code editor window (tab content)
		CodeEditorScrolledWindow = gtk.ScrolledWindow()
		CodeEditorScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		#code editor text object
		CodeEditorText = gtk.TextView()
		buffer = CodeEditorText.get_buffer()
		buffer.set_text(text)
		CodeEditorText.set_buffer(buffer)
		buffer.connect('changed',self.keyPressCodeEditor) #set callback function whenever text is changed
		CodeEditorText.show()
		CodeEditorScrolledWindow.add(CodeEditorText)
		CodeEditorScrolledWindow.show()

		#connect the close button
		closeButton.connect("clicked", self.ClosePage, CodeEditorScrolledWindow)

		if(label_name == 'Untitled'):
			return [CodeEditorScrolledWindow, labelBox, None]
		else:
			return [CodeEditorScrolledWindow, labelBox, label_name]
	
	#function to close the respective tab
	def ClosePage(self, widget, label):
		index = self.CodeNotebook.page_num(label)
		self.CodeNotebook.remove_page(index)
		del self.CodeNotebookPages[index]
		widget.destroy()

	#called when text is changed in the editor
	def keyPressCodeEditor(self,widget):
		self.HighlightKeywords()
		

	#function to go throught the text in the editor box and highlight keywords
	#removes all tags and reapplies them everytime a key is pressed
	#can be improved
	def HighlightKeywords(self):
		global keywords,tags
		#HIGHLIGHT KEYWORDS BELOW
		#get buffer
		page_num = self.CodeNotebook.get_current_page()
		buffer = self.CodeNotebookPages[page_num][0].get_children()[0].get_buffer()

		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()

		#remove tags from buffer and tagtable
		for tag in tags:
			buffer.remove_tag(tag,start_iter,end_iter)
			buffer.get_tag_table().remove(tag)
		#set tags list to empty list
		tags = []

		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()

		#highlight keywords
		for word in keywords:
			#search from beginning
			start_iter = buffer.get_start_iter()
			pos = start_iter.forward_search(word,gtk.TEXT_SEARCH_TEXT_ONLY)		
			#if search found
			while(pos != None):
				#check if the word is not a substring but an actual word
				if(pos[1].ends_word() and pos[0].starts_word()):
					tags.append(buffer.create_tag(None,foreground = '#ff0000'))
					buffer.apply_tag(tags[-1], pos[0], pos[1])
				#set iter to end position
				start_iter = pos[1]
				#search again
				pos = start_iter.forward_search(word,gtk.TEXT_SEARCH_TEXT_ONLY)		



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
		

	def CreateUrlBar(self):

		#TopFrame containing URL bar
		self.UrlBox = gtk.HBox()
		self.mainVerticalLayout.pack_start(self.UrlBox, fill = False, expand = False)
		#URL label
		self.UrlLabel = gtk.Label('URL :')
		self.UrlBox.pack_start(self.UrlLabel, fill = False, expand = False, padding = 5)
		#URL entry box
		self.UrlTextView = gtk.TextView()
		self.UrlTextView.connect('key_release_event',self.onPressEnterUrlBar)
		self.UrlTextView.set_events(gtk.gdk.KEY_RELEASE_MASK)
		self.UrlBox.pack_start(self.UrlTextView,padding = 5)

		self.UrlButton = gtk.Button("GO")
		self.UrlButton.connect('clicked',self.getTestCases)
		self.UrlBox.pack_start(self.UrlButton,False,False,padding = 5)


	#fetch test cases from url and add to input output boxes
	def getTestCases(self,widget):
		inputbuffer = self.InputText.get_buffer()
		inputbuffer.set_text('')
		self.InputText.set_buffer(inputbuffer)

		outputbuffer = self.OutputText.get_buffer()
		outputbuffer.set_text('')
		self.OutputText.set_buffer(outputbuffer)


		urlVal = self.UrlView.get_buffer().get_text()
		io = getInputOutput(urlVal)

		inputbuffer.set_text(io[0])
		self.InputText.set_buffer(inputbuffer)
		outputbuffer.set_text(io[1])
		self.OutputText.set_buffer(outputbuffer)


	#called when Enter is pressed on the URL bar
	def onPressEnterUrlBar(self,widget,event):
		if(event.keyval == 65293):
			self.getTestCases(None)


	#MENU BAR FUNCTIONS BELOW

	def CreateMenuBar(self):

		#Create file menu options
		self.FileMenu = gtk.Menu()
		self.NewFile = gtk.MenuItem("New")
		self.OpenFile = gtk.MenuItem("Open")
		self.SaveFile = gtk.MenuItem("Save")
		self.SaveAsFile = gtk.MenuItem("Save As")
		self.Quit = gtk.MenuItem("Quit")
		self.FileMenu.append(self.NewFile)
		self.FileMenu.append(self.OpenFile)
		self.FileMenu.append(self.SaveFile)
		self.FileMenu.append(self.SaveAsFile)
		self.FileMenu.append(self.Quit)
		#connect click functions
		self.NewFile.connect("activate", self.OpenNewFileDialog)
		self.OpenFile.connect("activate", self.OpenFileDialog)
		self.SaveFile.connect("activate", self.SaveFileDialog)
		self.SaveAsFile.connect("activate", self.SaveAsFileDialog)
		self.Quit.connect("activate", self.QuitApp)
		self.NewFile.show()
		self.OpenFile.show()
		self.SaveFile.show()
		self.SaveAsFile.show()
		self.Quit.show()

		# setting hotkeys
		accel_group = gtk.AccelGroup()
		self.mainWindow.add_accel_group(accel_group)
		self.OpenFile.add_accelerator("activate", accel_group, ord('O'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.SaveFile.add_accelerator("activate", accel_group, ord('S'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Quit.add_accelerator("activate", accel_group, ord('Q'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.NewFile.add_accelerator("activate", accel_group, ord('N'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

		#menu item file
		self.FileOption = gtk.MenuItem("File")
		self.FileOption.show()
		self.FileOption.set_submenu(self.FileMenu)

		#Create Edit Menu
		self.EditMenu = gtk.Menu()
		self.Preferences = gtk.MenuItem("Preferences")
		self.Cut = gtk.MenuItem("Cut")
		self.Copy = gtk.MenuItem("Copy")
		self.Paste = gtk.MenuItem("Paste")
		self.EditMenu.append(self.Cut)
		self.EditMenu.append(self.Copy)
		self.EditMenu.append(self.Paste)
		self.EditMenu.append(self.Preferences)
		self.Cut.connect("activate",self.CutText)
		self.Copy.connect("activate",self.CopyText)
		self.Paste.connect("activate",self.PasteText)
		self.Preferences.connect("activate",self.PreferencesResponse)
		self.Cut.show()
		self.Preferences.show()

		self.Cut.add_accelerator("activate", accel_group, ord('X'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Copy.add_accelerator("activate", accel_group, ord('C'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		self.Paste.add_accelerator("activate", accel_group, ord('V'),gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

		#menu edit item
		self.EditOption = gtk.MenuItem("Edit")
		self.EditOption.show()
		self.EditOption.set_submenu(self.EditMenu)

		#create menu bar
		self.MenuBar = gtk.MenuBar()
		self.mainVerticalLayout.pack_start(self.MenuBar, fill = False, expand = False)
		self.MenuBar.show()
		
		#add file options to menu bar		
		self.MenuBar.append(self.FileOption)
		self.MenuBar.append(self.EditOption)

	#function to paste text into the editor from clipboard
	def PasteText(self,widget):
		
		child = self.mainWindow.get_focus()
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
		buffer = child.get_buffer()
		clipboard = gtk.Clipboard()
		buffer.cut_clipboard(clipboard,True)

	#Response on clicking preferences in edit menu
	def PreferencesResponse(self, widget):

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
		self.PreferencesOpacityEntry.connect('changed', self.checkOpacityEntry) #connect to function to validate values
		self.PreferencesOpacityEntry.show()
		hbox.pack_start(self.PreferencesOpacityEntry)
		hbox.show()
		self.PreferencesDialog.vbox.pack_start(hbox,padding = 5)
		

		#add cancel button
		button = self.PreferencesDialog.add_button("Cancel",gtk.RESPONSE_ACCEPT)
		button.connect("clicked",self.ClosePreferences) #close the box on clicking cancel
		button.show()

		#add apply button
		button = self.PreferencesDialog.add_button("Apply",gtk.RESPONSE_ACCEPT)
		button.connect("clicked",self.ApplyPreferences)
		button.show()

		self.PreferencesDialog.run()

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

	#close the dialog box
	def ClosePreferences(self,widget):
		self.PreferencesDialog.destroy()

	#apply all preferences and close the box
	def ApplyPreferences(self,widget):
		#set opacity
		val = float(self.PreferencesOpacityEntry.get_text())
		self.mainWindow.set_opacity(val)
		self.PreferencesDialog.destroy()
		

	def OpenNewFileDialog(self,widget):

		page = self.CreateNotebookPage()
		self.CodeNotebook.append_page(page[0],page[1])
		self.CodeNotebookPages.append(page)
		self.CodeNotebook.set_current_page(-1)


	def OpenFileDialog(self, widget):

		dialog = gtk.FileChooserDialog("Open..", None, gtk.FILE_CHOOSER_ACTION_OPEN, 
											(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		response = dialog.run()
		if response == gtk.RESPONSE_OK:

			filestream = open(dialog.get_filename())
			filename = dialog.get_filename()
			text = filestream.read()
			filestream.close()

			page = self.CreateNotebookPage(filename[filename.rfind('/')+1:], text)
			self.CodeNotebookPages.append(page)
			self.CodeNotebook.append_page(page[0], page[1])		

		elif response == gtk.RESPONSE_CANCEL:
			print('Closed, no files selected') #log
		dialog.destroy()
		self.CodeNotebook.set_current_page(-1)


	def SaveAsFileDialog(self, widget):

		dialog = gtk.FileChooserDialog("Save As..", None, gtk.FILE_CHOOSER_ACTION_SAVE,
											(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		response = dialog.run()
		if response == gtk.RESPONSE_OK:

		    filestream = open(dialog.get_filename(),'w')
		    filename = dialog.get_filename()

		    page_num = self.CodeNotebook.get_current_page()
		    buffer = self.CodeNotebookPages[page_num][0].get_children()[0].get_buffer()

		    filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
		    filestream.close()

		    self.CodeNotebookPages[page_num][1].get_children()[0].set_label(filename[filename.rfind('/')+1:])
		    self.CodeNotebookPages[page_num][2] = filename[filename.rfind('/')+1:]

		elif response == gtk.RESPONSE_CANCEL:
		    print('Closed, no files selected') #log

		dialog.destroy()


	def QuitApp(self,widget):
		gtk.main_quit()


	def SaveFileDialog(self, widget):

		page_num = self.CodeNotebook.get_current_page()
		print(self.CodeNotebookPages[page_num])
		filename =  self.CodeNotebookPages[page_num][2]

		if(filename == None):
			dialog = gtk.FileChooserDialog("Save As..", None, gtk.FILE_CHOOSER_ACTION_SAVE,
											(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
			dialog.set_default_response(gtk.RESPONSE_OK)
			response = dialog.run()
			if response == gtk.RESPONSE_OK:
				filestream = open(dialog.get_filename(),'w')
				filename = dialog.get_filename()

				page_num = self.CodeNotebook.get_current_page()
				print("\ncurrent page : "+str(page_num)+'\n')
				buffer = self.CodeNotebookPages[page_num][0].get_children()[0].get_buffer()

				filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
				filestream.close()

				self.CodeNotebookPages[page_num][1].get_children()[0].set_label(filename[filename.rfind('/')+1:])
			elif response == gtk.RESPONSE_CANCEL:
				print('Closed, no files selected') #log
			dialog.destroy()
		else:
			filestream = open(filename,'w')
			
			page_num = self.CodeNotebook.get_current_page()
			buffer = self.CodeNotebookPages[page_num][0].get_children()[0].get_buffer()
			
			filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
			filestream.close()

			self.CodeNotebookPages[page_num][1].get_children()[0].set_label(filename[filename.rfind('/')+1:])




	#TOOLBAR FUNCTIONS BELOW

	#creates and adds the toolbar to the window
	def CreateToolBar(self):

		#Toolbar box
		self.ToolBarBox = gtk.HBox()
		self.mainVerticalLayout.pack_start(self.ToolBarBox, fill = False, expand = False)
		#Compile and run button
		self.CompileRunButton = gtk.Button('Compile&Run')
		self.CompileRunButton.connect('clicked',self.CompileRunCode)
		self.ToolBarBox.pack_start(self.CompileRunButton, fill = False, expand = False, padding = 5)

	#function called when compile&run button is click
	def CompileRunCode(self,widget):

		#write code to file
		codefile = open('tempcode.cpp','w')
		page_num = self.CodeNotebook.get_current_page()
		buffer = self.CodeNotebookPages[page_num][0].get_children()[0].get_buffer()
		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()
		text = buffer.get_text(start_iter,end_iter,True)
		codefile.write(text)
		codefile.close()

		#set label to compiling
		

		#perform compilation
		stream = subprocess.Popen(['g++','tempcode.cpp'],stdout = subprocess.PIPE,stdin = subprocess.PIPE,stderr= subprocess.PIPE)

		#get output/err
		output,err = stream.communicate()

		#if no output and no error => compilation successful
		if(output == '' and err == ''):

			print("compilation successfull") #log
			buffer = gtk.TextBuffer()
			buffer.set_text("Compilation Successful")
			self.CompilerText.set_buffer(buffer)

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
				buffer = gtk.TextBuffer()
				buffer.set_text("Run Successful")
				self.CompilerText.set_buffer(buffer)

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
					buffer = gtk.TextBuffer()
					buffer.set_text(userOutput+"\n ******** \noutput Correct(matches)")
					self.CompilerText.set_buffer(buffer)
				else:
					print("output incorrect") #log
					buffer = gtk.TextBuffer()
					buffer.set_text(userOutput+"\n ******** \noutput Incorrect (does not match)")
					self.CompilerText.set_buffer(buffer)
					

			else: #show runtime error
				print("runtime error")
				print(err) #log
				buffer = gtk.TextBuffer()
				buffer.set_text("RUNTIME ERROR : \n"+err)
				self.CompilerText.set_buffer(buffer)
				
				
		else: #show compilation error
			print("compilation error")
			print(err) #log
			buffer = gtk.TextBuffer()
			buffer.set_text("COMPILATION ERROR : \n"+err)
			self.CompilerText.set_buffer(buffer)	
			
			

		#remove the temporary code file and run file
		stream = subprocess.Popen(['rm','a.out'])
		stream = subprocess.Popen(['rm','tempcode.cpp'])

		print('files deleted') #log		

#loads keywords (currently only cpp)
def loadKeywords():

	global keywords

	f = open('cppkeywords.txt','r')
	keywords = f.readlines()
	for i in range(0,len(keywords)):
		keywords[i] = keywords[i].rstrip()

if __name__ == "__main__":

	loadKeywords()
	window = MainWindow()