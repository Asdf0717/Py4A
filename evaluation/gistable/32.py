import os
import re
import hashlib
import urllib.request

class ImgurDownloader:
    destinationFolder = 'D:\\imgur-downloads\\'
    pattern = re.compile('<img alt="" src="//([^"]+)"')
    
    def __init__(self, category):
        self.category = category
        if not os.path.exists(self.destinationFolder):
            os.makedirs(self.destinationFolder)

    def getImgurLink(self):
        return "https://imgur.com/r/%s/top/month" %self.category

    def getImages(self):
        resource = urllib.request.urlopen(self.getImgurLink())
        source = resource.read().decode(resource.headers.get_content_charset())
        matches = self.pattern.findall(source)
        return list(map(lambda link: "https://" + link, matches))

    def getDestination(self, imgurLink):
        return self.destinationFolder + hashlib.sha224(imgurLink.encode()).hexdigest() + ".jpg"

    def download(self):
        images = self.getImages()
        print("Found %i images" %len(images))
        for image in images:
            destination = self.getDestination(image)
            print(image + " --> " + destination)
            urllib.request.urlretrieve(image, destination)
        
downloader = ImgurDownloader("cats")
print("About to download from " + downloader.getImgurLink())
downloader.download()
