#!/usr/bin/env python3
import numpy as np
import logging
import pyclamster
import pysolar
import os,glob,re
import datetime,pytz
import pickle

logging.basicConfig(level=logging.DEBUG)

# position of wolf-1 camera
LAT = 53.99777
LON = 9.56673


###################################################
### Read times and sun positions from filenames ###
###################################################
files = glob.glob("examples/images/wolf/calibration/*")
files.sort()

elevations= []
azimuths  = []
sunrows   = []
suncols   = []
for imgfile in files:
    # read image
    #img = pyclamster.image.Image(imgfile)
    # read time from filename
    name = os.path.basename(imgfile)
    r = re.compile('^Wolf_(\w+)_UTC[^_]+_sunrow(\d+)_suncol(\d+)')
    m = r.match(name)
    timestr  = m.group(1)
    sunrow   = np.float(m.group(2))
    suncol   = np.float(m.group(3))
    fmt = "%Y%m%d_%H%M%S"
    time = pytz.utc.localize(datetime.datetime.strptime(timestr,fmt))
    time = time - datetime.timedelta(hours=1)
    logging.debug(time)
    ele  = pysolar.solar.get_altitude(LAT,LON,time)
    azi  = abs(pysolar.solar.get_azimuth(LAT,LON,time))
    elevations.append(ele)
    azimuths.append(azi)
    sunrows.append(sunrow)
    suncols.append(suncol)
    logging.debug("{file}: ele: {ele}, azi: {azi}, sunrow: {row}, suncol: {col}".format(
        file=imgfile,ele=ele,azi=azi,row=sunrow,col=suncol))

##############################
### Pre-process input data ###
##############################
# convert and preprocess input
sunrows = np.asarray(sunrows)
suncols = np.asarray(suncols)

# convert azimuth to radiant
azimuths   = pyclamster.deg2rad(np.asarray(azimuths))
# project azimuth on (0,2*pi)
azimuths = (azimuths + 2*np.pi) % (2*np.pi)

# convert elevation to angle from zenith 
elevations = np.pi/2 - pyclamster.deg2rad(np.asarray(elevations))


#####################################################
### Merge input data into Coordinates3d instances ###
#####################################################
# sun coordinates on the image plane based on (row, col)
pixel_coords = pyclamster.Coordinates3d(
    x = suncols, y = 1920 - sunrows, # TODO: HARD CODED shape here!!!
    azimuth_clockwise = False,
    azimuth_offset=np.pi/2
    )

# real sun cooridnates based on (elevation,azimuth)
sun_coords = pyclamster.Coordinates3d(
    elevation = elevations, azimuth = azimuths,
    azimuth_offset = 3*np.pi/2,
    azimuth_clockwise = False
    )


#######################################
### Prepare and do the optimization ###
#######################################
# first guess for parameters
params_firstguess = pyclamster.CameraCalibrationParameters(
    960, # center_row
    960, # center_col
    0, # north_angle
    600, # r0
    100, # r0
    0, # r0
    0, # r0
    )

# create a lossfunction
lossfunction = pyclamster.calibration.CameraCalibrationLossFunction(
    pixel_coords = pixel_coords, sun_coords = sun_coords,
    radial = pyclamster.FisheyeEquidistantRadialFunction(params_firstguess)
    )

# create calibrator
calibrator = pyclamster.CameraCalibrator(method="l-bfgs-b")


# let the calibrator estimate a calibration
calibration = calibrator.estimate(lossfunction, params_firstguess)

# print the results
logging.debug(calibration.fit)
logging.debug(calibration.parameters)

filename = "examples/calibration/wolf-3-calibration.pickle"
logging.debug("pickling calibration to file '{}'".format(filename))
fh = open(filename,'wb')
pickle.dump(calibration,fh)
fh.close()

cal_coords=calibration.create_coordinates((1920,1920))
cal_coords.z = 1 # assume a height to see x and y

import matplotlib.pyplot as plt
plt.subplot(221)
plt.title("[calibrated]\nelevation on the image")
plt.imshow(cal_coords.elevation)
plt.colorbar()
plt.subplot(222)
plt.title("[calibrated]\nazimuth on the image")
plt.imshow(cal_coords.azimuth)
plt.colorbar()
plt.subplot(223)
plt.title("[calibrated]\n[z=1 plane]\nreal-world x on the image")
plt.imshow(cal_coords.x)
plt.colorbar()
plt.subplot(224)
plt.title("[calibrated]\n[z=1 plane]\nreal-world y on the image")
plt.imshow(cal_coords.y)
plt.colorbar()
plt.show()