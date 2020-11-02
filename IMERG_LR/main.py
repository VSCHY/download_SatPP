import sys
import requests 
from datetime import date, timedelta
import numpy as np 
import os 
import subprocess
import time
import multiprocessing
import random
import glob
from imerg_func import *
import download_function as down
from calendar import monthrange
import configparser

config=configparser.ConfigParser()
config.read("config.def")
output=config.get("OverAll", "output")
temp_dir=config.get("OverAll", "temp_dir")

##########################################

class download:
    def __init__(self, output, temp_dir):
        self.output = output
        self.temp_dir = temp_dir
        os.chdir(self.temp_dir)

    def download_month(self, year, month):
      output = self.output+"{0}/{1:02}/".format(year, month)
      # 
      if not os.path.exists(output):
          os.makedirs(output)
      dmon = self.output+"{0}/".format(year, month)+"3B-HHR-L.MS.MRG.3IMERG.daily.month"+str(month).zfill(2)+str(year)+".nc"
      if not os.path.isfile(dmon):

        d = monthrange(year, month)[1]
        for i in range(1,d+1):
            t0 = time.time()
            if len([name for name in os.listdir(temp_dir) if os.path.isfile(name)])>0:
                down.empty_directory(temp_dir)
            datet = "{0}{1:02}{2:02}".format(year, month, i)
            filen = output+"3B-HHR-L.MS.MRG.3IMERG."+datet+".nc"
            if __name__ == "__main__":
                pool = multiprocessing.Pool(processes=4)
            if not os.path.isfile(filen):  
                L = down.get_HH_urls_day(year, month, i)
                numfile = 0
                while numfile <48:
                    if __name__ == "__main__":
                        pool.map(down.download, L)
                        numfile = len([name for name in os.listdir('.') if os.path.isfile(name)])
                if __name__ == "__main__":
                    pool.close()
                ds = imerg_xarray_from_date(temp_dir, "{0}-{1}-{2}".format(year,month,i), "Late")
                ds.to_netcdf(path=filen, unlimited_dims = ["time"])
                ds.close()
                t1 = time.time()
                print("FINAL TIME - {0}/{1}/{2}".format(i,month,year), int(t1-t0), "s.")
        subprocess.check_call(["cdo", "mergetime",output+"*.nc", dmon])
        down.empty_directory(output)
        
##########################################

if __name__ == "__main__":
    d = download(output,temp_dir)
    # Define list of years
    # ex : YEAR = [2019]
    YEAR = []
    # Define list of months
    # ex : MONTH = np.arange(1,12)
    ONTH = np.arange(1,12)
    for y in YEAR
        for m in MONTH:
            d.download_month(y, m)

