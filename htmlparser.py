import urllib2

def getInputOutput(url):

	url = url.rstrip()
	print("url : "+url)

	val = []
	try:
		response = urllib2.urlopen(url)
	except:
		return ["Error occured. Retry or copy paste manually","Connection Error. Retry or copy paste manually"]
	source = response.read()

	if(url.find('www.codechef.com') >= 0 ):
		return codechef(source)

	return val


def codechef(source):

	val = []
	
	start = source.find('<pre>')
	start += 5
	stop = source.find('</pre>')
	source = source[start:stop]

	print(source)

	#get input
	if(source.find('<b>Input</b>') >= 0):
		start = source.find('<b>Input</b>') + len('<b>Input</b>') + 1
	elif(source.find('<b>Input:</b>') >= 0):
		start = source.find('<b>Input:</b>') + len('<b>Input:</b>') + 1

	if(source.find('<b>Output</b>') >= 0):
		stop = source.find('<b>Output</b>')
	elif(source.find('<b>Output:</b>') >= 0):
		stop = source.find('<b>Output:</b>')

	inp = source[start:stop]

	while(inp[-1] == '\n'):
		inp = inp[0:-1]
	inp+='\n'

	val.append(inp)


	#get output
	if(source.find('<b>Output</b>') >= 0):
		start = source.find('<b>Output</b>') + len('<b>Output</b>') + 1
	elif(source.find('<b>Output:</b>') >= 0):
		start = source.find('<b>Output:</b>') + len('<b>Output:</b>') + 1

	out = source[start:]

	while(out[-1] == '\n'):
		out = out[0:-1]
	out+='\n'

	val.append(out)

	return val