import urllib2
import re
import threading

class crawler_thread(threading.Thread):
	def __init__(self, url, filepath):
		threading.Thread.__init__(self)
		self.url = url
		self.filepath = filepath
	def run(self):
		fid = open(self.filepath, 'w')
		fid.write(urllib2.urlopen(self.url).read())
		fid.close()

# download html containing file links
download_directory = '/Users/qiao/Dropbox/cse546/slides/'
source_html_url = 'http://courses.cs.washington.edu/courses/cse546/13au/schedule.html'

# get html
source_html = urllib2.urlopen(source_html_url).read()

# find all filenames
file_url_pattern = re.compile('slides/.*annotated.pdf')
list_filenames = file_url_pattern.findall(source_html)

# compile full url for each filenames
threads = []
base_url = 'http://courses.cs.washington.edu/courses/cse546/13au/'
for filename in list_filenames:
	url = base_url + filename
	filename_on_disk = download_directory + filename.split('/')[1]
	t = crawler_thread(url, filename_on_disk)
	t.start()
	threads.append(t)

for t in threads:
	t.join()
