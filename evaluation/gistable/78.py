# -*- coding:utf-8 -*-
#import numpy
from PIL import Image

class Dither:
    def __init__(self,image_path):
       self.imgdata = Image.open(image_path).resize((128,128)).convert("L")
       #self.imgarray = numpy.asarray(self.imgdata)

    def error_diffusion(self):
        data = self.imgdata.convert(mode="1",dither=1)
        #maxcol, maxrow = self.imgdata.size
        #outarray = numpy.copy(self.imgarray)
        #self.imgarray.flags.writeable = True
        
        #for i in xrange(maxrow):
        #    for j in xrange(maxcol):
        #        if self.imgarray[i,j] > 0 :
        #            outarray[i,j] = 1
        #        else:
        #            outarray[i,j] = 0
                #print( str(self.imgarray[i,j]) +"," + str(outarray[i,j]))

                #error = 0
                
                #if self.imgarray[i,j] > 127:
                #    eroor = self.imgarray[i,j] -255
                #    outarray[i,j] = 1
                #else:
                #    eroor = self.imgarray[i,j]
                #    outarray[i,j] = 0
                
                #if(i+1 != maxrow):
                #    self.imgarray[i+1][j] += 5/16 * error
                #    if(j+1 != maxcol):
                #        self.imgarray[i+1][j+1] += 3/16 * error
                #if(j+1 != maxcol):
                #    self.imgarray[i][j+1] += 5/16 * error
                #    if(i != 0):
                #         self.imgarray[i-1][j+1] += 3/16 * error
        
        #data = self.decode_img(numpy.uint8(outarray))
        
        return data

    def decode_img(self,img_array):
        return Image.fromarray(img_array,mode="1")