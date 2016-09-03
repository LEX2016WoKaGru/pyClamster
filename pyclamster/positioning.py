# -*- coding: utf-8 -*-
"""
Created on 03.09.16

Created for pyclamster

    Copyright (C) {2016}

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# System modules
import logging

# External modules
import numpy as np

# Internal modules
from . import coordinates


logger = logging.getLogger(__name__)

__version__ = "0.1"


def doppelanschnitt(azi1,azi2,ele1,ele2,pos1,pos2):
    """
    calculate the 3d position via "doppelanschnitt"

    args:
        azi1, azi2, ele1, ele2 (float): SINGLE values of azimuth and elevation
            of different devices at positions 1 and 2 (radians)
        pos1, pos2 (np.array) [x,y,z] of different devices at positions
            1 and 2 (metres)

    returns:
        
    """

    e1 = np.array([np.sin(azi1)*np.cos(ele1),
                   np.cos(azi1)*np.cos(ele1),
                   np.sin(ele1)])

    e2 = np.array([np.sin(azi2)*np.cos(ele2),
                   np.cos(azi2)*np.cos(ele2),
                   np.sin(ele2)])

    n = np.cross(e1,e2,axis=0)
    n = n/np.linalg.norm(n)

    a,b,c = np.linalg.solve(np.array([e1,e2,n]).T,
        (np.array(pos1)-np.array(pos2)).T)

    position = np.array(pos1 - a * e1 - n * 0.5 * c)


    return position


# multiple values
def doppelanschnitt_Coordinates3d(aziele1,aziele2,pos1,pos2):
    """
    calculate 3d position based on Coordinates3d

    args:
        aziele1,aziele2 (Coordinates3d): coordinates (azimuth/elevation) of 
            devices 1 and 2. These have to be northed
        pos1, pos2 (Coordinates3d): length 1 coordinates (x,y,z) of devices
            1 and 2

    returns:
        positions (Coordinates3d): (x,y,z) positions taken from
            Doppelanschnitt.
    """
    # turn to north
    aziele1.change_parameters(
        azimuth_offset = 3/2 * np.pi, azimuth_clockwise = True,
        elevation_type = "ground",
        keep = {'azimuth','elevation'}
        )

    logger.debug("aziele1: \n{}".format(aziele1))
    aziele2.change_parameters(
        azimuth_offset = 3/2 * np.pi, azimuth_clockwise = True,
        elevation_type = "ground",
        keep = {'azimuth','elevation'}
        )
    logger.debug("aziele2: \n{}".format(aziele2))

    # convert given positions to numpy array
    position1 = np.array([pos1.x,pos1.y,pos1.z])
    logger.debug("position1: \n{}".format(position1))
    position2 = np.array([pos2.x,pos2.y,pos2.z])
    logger.debug("position2: \n{}".format(position2))

    # loop over all azimuth/elevation values
    x = [];y = [];z = [] # start with empty lists
    for azi1,azi2,ele1,ele2 in zip(
        aziele1.azimuth, aziele2.azimuth, aziele1.elevation, aziele2.elevation):
        # calculate 3d doppelanschnitt position
        xnew, ynew, znew = doppelanschnitt(
            azi1=azi1,azi2=azi2,ele1=ele1,ele2=ele2,
            pos1=position1,pos2=position2)

        x.append(xnew)
        y.append(ynew)
        z.append(znew)

    # merge new coordinates
    out = coordinates.Coordinates3d(x=x,y=y,z=z,shape = aziele1.shape)

    return out