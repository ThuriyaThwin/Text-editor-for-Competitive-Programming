


class PageVals():

	def __init__(self, scrolledWindow, labelBox, filepath, saveState, textStates, undoThreadOn, undoRedoIndex, tags):

		# [scrolledwindow object, labelbox object, filepath, save state, undoStates, undoThreadOn]

		#holds the scrolled window object
		self.scrolledWindow = scrolledWindow # 0
		#holds the label box in the tab
		self.labelBox = labelBox # 1
		#holds the path of the file
		self.filepath = filepath # 2
		#True if file is saved up to date, false if unsaved changes are mades
		self.saveState = saveState # 3
		#holds the state of previous undo points
		self.textStates = textStates # 4
		#true if undo thread is running
		self.undoThreadOn = undoThreadOn # 5
		#holds the index at which undo/redo is to be done
		self.undoRedoIndex = undoRedoIndex #6
		#holds the tags created in the page
		self.tags = tags # 7
