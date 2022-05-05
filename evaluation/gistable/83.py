from PIL import Image, ImageOps
import clipboard, photos,webbrowser
im=photos.pick_image()#clipboard.get_image
if im.size[0] >= im.size[1]:
	whitespace=((im.size[0]-im.size[1])/2)+250
	xbump=250
else:
	xbump=((im.size[1]-im.size[0])/2)+250
	whitespace=250
matted=ImageOps.expand(im,border=(xbump,whitespace),fill='white')
photos.save_image(matted)
inst='instagram://camera'
webbrowser.open(inst)
#if you have any questions or comments @jamescampbell on twitter