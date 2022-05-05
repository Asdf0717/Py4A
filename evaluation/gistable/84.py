import urllib2
import cv2
from bs4 import BeautifulSoup
import os


def download_NASA_APOD_wallpaper(save_path, width=1366, height=768):
    browser = urllib2.urlopen("http://apod.nasa.gov/apod/astropix.html")
    html = BeautifulSoup(browser.read())
    browser.close()
    image_link = "http://apod.nasa.gov/apod/" + \
        html.find("img").parent.get("href")
    image_name = image_link.split("/")[-1]
    store_path = os.path.dirname(save_path) + "/" + image_name

    if os.path.isfile(store_path):
        return

    browser = urllib2.urlopen(image_link)
    image_file = open(save_path, "wb")
    image_file.write(browser.read())
    image_file.close()
    browser.close()

    img = cv2.imread(save_path)
    rows, cols, _ = img.shape
    if (float(cols) / rows) < (float(width) / height):
        img = cv2.resize(img, (width, int(float(width) / cols * rows)))
        cut = img.shape[0] - height
        img = img[int(cut / 2):(int(cut / 2) + height), :, :]
    else:
        img = cv2.resize(img, (int(float(height) / rows * cols), height))
        cut = img.shape[1] - width
        img = img[:, int(cut / 2):(int(cut / 2) + width), :]

    cv2.imwrite(save_path, img)
    os.system("cp \"" + save_path + "\" \"" + store_path + "\"")
    os.system("cp \"" + save_path + "\" ~/.xmonad/Wallpaper.jpg")
    os.system("cp \"" + save_path + "\" ~/Pictures/Wallpaper.jpg")
    os.system("feh --bg-scale ~/Pictures/Wallpaper.jpg")
    os.system("gsettings set com.canonical.unity-greeter background " +
              "'~/Pictures/Wallpaper.jpg'")
    os.system("gsettings set org.gnome.desktop.background picture-uri " +
              "'file:///~/Pictures/Wallpaper.jpg'")


if __name__ == "__main__":
    download_NASA_APOD_wallpaper("~/Pictures/APOD/Wallpaper.jpg")