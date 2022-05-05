import os

from PIL import Image, ImageOps

def resize_image(path, box, out=None, fit=True, quality=75):
    """ Downsample an image.

        @param path:    string - path to the original image
        @param box:     tuple(x, y) - the bounding box of the result image
        @param out:     file-like-object - save the image into the output stream
        @param fit:     boolean - crop the image to fill the box
        @param quality: int - JPEG quality
    """
    img = Image.open(path)
    if fit:
        img = ImageOps.fit(img, box, Image.ANTIALIAS)
    else:
        img.thumbnail(box, Image.ANTIALIAS)
    if not out:
        out = os.path.splitext(path)[0] + ".tn.jpg"
    img.save(out, "JPEG", quality=quality)
