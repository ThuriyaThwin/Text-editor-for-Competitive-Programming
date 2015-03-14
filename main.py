import gtk
import os
import subprocess
import re
import string
from htmlparser import *

keywords = []
tags = []
filename = None

class MainWindow():

	def __init__(self):

		self.init()

	def init(self):

		self.mainWindow = gtk.Window()
		self.mainWindow.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#696969'))
		self.mainWindow.set_position(gtk.WIN_POS_CENTER)
		self.mainWindow.set_default_size(200,200)
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

	def WindowResize(self,widget,allocation):

		#adjust pane bar between IO window
		self.IOPanedWindow.set_position(int(allocation.width*0.5))
		#adjust pane bar between IO window and code editor window
		self.IOCodeWindow.set_position(int(allocation.height*0.2))
		#adjust pane bar between IO,codeeditor and compiler output window
		self.CenterWindow.set_position(int(allocation.height*0.8))


	def CreateCompilerBox(self):

		#create a scrolled window for compiler/run output
		self.CompilerScrolledWindow = gtk.ScrolledWindow()
		self.CompilerScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.CompilerText = gtk.TextView()
		self.CompilerText.set_editable(False)
		self.CompilerScrolledWindow.add(self.CompilerText)
		#add to center window(VPaned)
		self.CenterWindow.add(self.CompilerScrolledWindow)

	def CreateCodeEditorBox(self):

		#Box to hold CodeEditor
		self.CodeEditorBox = gtk.HBox()
		#scrolled window to hold code editor
		self.CodeEditorScrolledWindow = gtk.ScrolledWindow()
		self.CodeEditorScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		#code editor text object
		self.CodeEditorText = gtk.TextView()
		self.CodeEditorScrolledWindow.add(self.CodeEditorText)
		self.CodeEditorBox.pack_start(self.CodeEditorScrolledWindow,padding = 5)
		#adding the code editor scrolled window to vertical pannable window
		self.IOCodeWindow.add(self.CodeEditorBox)
		#TODO function to auto set the position when window size changes

		self.CodeEditorText.connect('key_release_event',self.keyPressCodeEditor)
		self.CodeEditorText.set_events(gtk.gdk.KEY_RELEASE_MASK)

	def keyPressCodeEditor(self,widget,event):

		self.HighlightKeywords()
		

	def HighlightKeywords(self):
		global keywords,tags
		#HIGHLIGHT KEYWORDS BELOW
		#get buffer
		buffer = self.CodeEditorText.get_buffer()

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
		self.UrlEntry = gtk.Entry()
		self.UrlEntry.connect('key_release_event',self.onPressEnterUrlBar)
		self.UrlEntry.set_events(gtk.gdk.KEY_RELEASE_MASK)
		self.UrlBox.pack_start(self.UrlEntry,padding = 5)

	def onPressEnterUrlBar(self,widget,event):
		if(event.keyval == 65293):
			print("enter pressed")
			inputbuffer = self.InputText.get_buffer()
			inputbuffer.set_text('')
			self.InputText.set_buffer(inputbuffer)

			outputbuffer = self.OutputText.get_buffer()
			outputbuffer.set_text('')
			self.OutputText.set_buffer(outputbuffer)


			urlVal = self.UrlEntry.get_text()
			io = getInputOutput(urlVal)

			inputbuffer.set_text(io[0])
			self.InputText.set_buffer(inputbuffer)
			outputbuffer.set_text(io[1])
			self.OutputText.set_buffer(outputbuffer)

	def CreateToolBar(self):

		#Toolbar box
		self.ToolBarBox = gtk.HBox()
		self.mainVerticalLayout.pack_start(self.ToolBarBox, fill = False, expand = False)
		#Compile and run button
		self.CompileRunButton = gtk.Button('Compile&Run')
		self.CompileRunButton.connect('clicked',self.CompileRunCode)
		self.ToolBarBox.pack_start(self.CompileRunButton, fill = False, expand = False, padding = 5)


	def CreateMenuBar(self):

		#Create file menu options
		self.FileMenu = gtk.Menu()
		self.OpenFile = gtk.MenuItem("Open")
		self.SaveFile = gtk.MenuItem("Save")
		self.SaveAsFile = gtk.MenuItem("Save As")
		self.Quit = gtk.MenuItem("Quit")
		self.FileMenu.append(self.OpenFile)
		self.FileMenu.append(self.SaveFile)
		self.FileMenu.append(self.SaveAsFile)
		self.FileMenu.append(self.Quit)
		#connect click functions
		self.OpenFile.connect("activate", self.menuItemResponse, "Open")
		self.SaveFile.connect("activate", self.menuItemResponse, "Save")
		self.SaveAsFile.connect("activate", self.menuItemResponse, "SaveAs")
		self.Quit.connect("activate", self.menuItemResponse, "Quit")
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


		#menu item file
		self.FileOption = gtk.MenuItem("File")
		self.FileOption.show()
		self.FileOption.set_submenu(self.FileMenu)

		#create menu bar
		self.MenuBar = gtk.MenuBar()
		self.mainVerticalLayout.pack_start(self.MenuBar, fill = False, expand = False)
		self.MenuBar.show()

		#create file button
		self.FileButton = gtk.Button("File")
		self.FileButton.connect_object("event", self.MenuButtonPressed, self.FileMenu)
		self.FileButton.show()

		# self.MenuBarBox = gtk.HBox()
		# self.mainVerticalLayout.pack_start(self.MenuBarBox, fill = False, expand = False)
		# self.MenuBarBox.pack_start(self.FileButton, fill = False, expand = False)
		
		self.MenuBar.append(self.FileOption)



	def MenuButtonPressed(self, widget, event):
		if event.type == gtk.gdk.BUTTON_PRESS:
			widget.popup(None, None, None, event.button, event.time)
			return True
		return False

	def menuItemResponse(self, widget, string):
		global filename
		if(string == "Open"):
			dialog = gtk.FileChooserDialog("Open..", None, gtk.FILE_CHOOSER_ACTION_OPEN, 
											(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
			dialog.set_default_response(gtk.RESPONSE_OK)
			response = dialog.run()
			if response == gtk.RESPONSE_OK:

			    filestream = open(dialog.get_filename())
			    filename = dialog.get_filename()
			    text = filestream.read()
			    filestream.close()

			    buffer = self.CodeEditorText.get_buffer()
			    buffer.set_text(text)
			    self.CodeEditorText.set_buffer(buffer)

			elif response == gtk.RESPONSE_CANCEL:
			    print 'Closed, no files selected' #log
			dialog.destroy()

		elif(string == "SaveAs"):

			dialog = gtk.FileChooserDialog("Save As..", None, gtk.FILE_CHOOSER_ACTION_SAVE,
											(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
			dialog.set_default_response(gtk.RESPONSE_OK)
			response = dialog.run()
			if response == gtk.RESPONSE_OK:
			    filestream = open(dialog.get_filename(),'w')
			    filename = dialog.get_filename()
			    buffer = self.CodeEditorText.get_buffer()
			    filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
			    filestream.close()
			elif response == gtk.RESPONSE_CANCEL:
			    print 'Closed, no files selected' #log
			dialog.destroy()

		elif(string == "Quit"):
			gtk.main_quit()

		elif(string == "Save"):
			if(filename == None):
				dialog = gtk.FileChooserDialog("Save As..", None, gtk.FILE_CHOOSER_ACTION_SAVE,
												(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
				dialog.set_default_response(gtk.RESPONSE_OK)
				response = dialog.run()
				if response == gtk.RESPONSE_OK:
				    filestream = open(dialog.get_filename(),'w')
				    filename = dialog.get_filename()
				    buffer = self.CodeEditorText.get_buffer()
				    filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
				    filestream.close()
				elif response == gtk.RESPONSE_CANCEL:
				    print 'Closed, no files selected' #log
				dialog.destroy()
			else:
				filestream = open(filename,'w')
				buffer = self.CodeEditorText.get_buffer()
				filestream.write(buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter()))
				filestream.close()


	def CompileRunCode(self,widget):

		#write code to file
		codefile = open('tempcode.cpp','w')
		buffer = self.CodeEditorText.get_buffer()
		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()
		text = buffer.get_text(start_iter,end_iter,True)
		codefile.write(text)
		codefile.close()

		#set label to compiling
		

		#perform compilation
		stream = subprocess.Popen(['g++','tempcode.cpp'],stdout = subprocess.PIPE,stdin = subprocess.PIPE,stderr= subprocess.PIPE)

		#get output
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