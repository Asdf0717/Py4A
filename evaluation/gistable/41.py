import subprocess
import sys, re
MERC = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs'

infile = sys.argv[1]

info_output = subprocess.Popen(['gdalinfo', infile], stdout=subprocess.PIPE).communicate()[0]

size_is_re = re.compile('Size is (?P<width>\d+), (?P<height>\d+)')
size_is = filter(lambda x: x, map(lambda x: size_is_re.match(x), info_output.split('\n')))

if (len(size_is) != 1):
    raise 'Could not parse gdalinfo output for image size'

size = [float(size_is[0].group('width')), float(size_is[0].group('height'))]

aspect_ratio = size[1] / size[0]

# the full world dimension
dim = 20037508.34 * 2

if (aspect_ratio > 1):
    h = dim
    w = dim / aspect_ratio
else:
    h = dim * aspect_ratio
    w = dim

res = subprocess.call(['gdal_translate', '-a_ullr', str(-w/2), str(-h/2), str(w/2), str(h/2), '-a_srs', MERC, infile, '%s.tif' % infile])

if res != 0:
    raise 'An error occurred upon calling gdal_translate'
