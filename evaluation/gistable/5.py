import sys; from PIL import Image; import numpy as np

chars = np.asarray(list(' .,:;irsXA253hMHGS#9B&@'))

if len(sys.argv) != 4: print( 'Usage: ./asciinator.py image scale factor' ); sys.exit()
f, SC, GCF, WCF = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), 7/4

img = Image.open(f)
S = ( round(img.size[0]*SC*WCF), round(img.size[1]*SC) )
img = np.sum( np.asarray( img.resize(S) ), axis=2)
img -= img.min()
img = (1.0 - img/img.max())**GCF*(chars.size-1)

print( "\n".join( ("".join(r) for r in chars[img.astype(int)]) ) )