import urllib2
import bs4

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

	soup = bs4.BeautifulSoup(source)
	val = []
	for child in soup.find('pre').findChildren():
		val.append(child.next_sibling.strip())

	return val