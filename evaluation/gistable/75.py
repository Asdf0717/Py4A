#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Output Elevation, Lat, Long, and Timestamp series from GPX to CSV
Requires gpxpy
This script expects your input GPX to be located in a subdir named 'data'

"""

import os
import gpxpy
import gpxpy.gpx
import csv

outputdir = "output"
os.path.exists(outputdir) or os.makedirs(outputdir)

# put your GPX file in a subdir named 'data'
try:
    gpx_file = open(os.path.join("data", "input.gpx"), "r")
    gpx = gpxpy.parse(gpx_file)
except IOError:
    print("Couldn't open the input GPX file. Ensure it's in the 'data' dir.")
    raise()


def write_csv():
    """ coroutine for writing dicts to a CSV as rows """
    header_written = False
    # create a CSV writer object
    with open(os.path.join(outputdir, "output.csv"), "w") as f:
        while True:
            data = (yield)
            # don't bother writing anything unless we have GPS data
            dw = csv.DictWriter(f, sorted(data.keys()))
            if not header_written:
                dw.writeheader()
                header_written = True
            dw.writerow(data)

# initialise csv output co-routine
output = write_csv()
output.next()
# dump each lat/lon/elevation/timestamp into a dict, with a Unix timestamp
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            output.send({
                "Lat.": point.latitude,
                "Lon.": point.longitude,
                "Elev.": point.elevation,
                "Timestamp": point.time.isoformat()
            })
