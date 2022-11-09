# -*- coding: utf-8 -*-
"""
Created on Thu Jul 22 11:43:35 2021

@author: lenovo
"""

import numpy as np

def gps2ecef(lat,long,h):
    """
    From geodetic (latitude,longitude,height) to ECEF (x,y,z) coordinates

    Args:
    ----------

    lat : ArrayLike
           target geodetic latitude
    lon : ArrayLike
           target geodetic longitude
    h : ArrayLike
         target altitude above geodetic ellipsoid (meters)

    Returns:
    -------

    ECEF (Earth centered, Earth fixed)  x,y,z

    x : ArrayLike
        target x ECEF coordinate (meters)
    y : ArrayLike
        target y ECEF coordinate (meters)
    z : ArrayLike
        target z ECEF coordinate (meters)
    """    
    lat = lat * np.pi / 180
    long = long * np.pi / 180
    
    a = 6378137
    b = 6356752.314245
    # a, b from https://en.wikipedia.org/wiki/Earth_ellipsoid
    e = (a**2 - b**2) / a ** 2
    v = a / (1 - e**2 * np.cos(lat)**0.5)**0.5
    
    # 大地经纬度坐标（纬度j ，经度l ）和地心直角坐标 X、Y、Z 的转换
    x = (v + h) * np.cos(lat) * np.cos(long)
    y = (v + h) * np.cos(lat) * np.sin(long)
    z = ((1-e**2) * v + h) * np.sin(lat)
    return x,y,z


def ecef2enu(x,y,z,x_ref,y_ref,z_ref,lat0,long0):
    """
    From ECEF to ENU (east, north, up) 东北天坐标系
    
    Args:
    ----------
    x : ArrayLike
        target x ECEF coordinate (meters)
    y : ArrayLike
        target y ECEF coordinate (meters)
    z : ArrayLike
        target z ECEF coordinate (meters) 
        
    x_ref : ArrayLike
        Observer x ECEF coordinate (meters)
    y_ref : ArrayLike
        Observer y ECEF coordinate (meters)
    z_ref : ArrayLike
        Observer z ECEF coordinate (meters) 
    lat0 : ArrayLike
           Observer geodetic latitude
    lon0 : ArrayLike
           Observer geodetic longitude


    Returns:
    -------
    xEast : ArrayLike
        East ENU
    yNorth : ArrayLike
        North ENU
    zUp : ArrayLike
        Up ENU
    """
    lat0, long0 = lat0 * np.pi / 180, long0 * np.pi / 180
    
    x_d = x - x_ref
    y_d = y - y_ref
    z_d = z - z_ref
    
    
    # the firtst point as the reference point
    xEast = -np.sin(long0) * x_d + np.cos(long0) * y_d
    yNorth = -np.cos(long0) * np.sin(lat0) *  x_d - np.sin(lat0) * np.sin(long0) * y_d + np.cos(lat0) * z_d
    zUp = np.cos(lat0) * np.cos(long0) * x_d + np.cos(lat0) * np.sin(long0) * y_d + np.sin(lat0) * z_d    
    
    return xEast, yNorth, zUp
