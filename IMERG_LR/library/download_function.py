import sys
sys.path.append("/home/anthony/Documents/Doctorat/PROD/FELIX/CODE/GPM")
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
import configparser

#https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
# overriding requests.Session.rebuild_auth to mantain headers when redirected

class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)
 
   # Overrides from the library to keep headers when redirected to or from
   # the NASA auth host.
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url
        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']
        return
 

# Get username and password from the config.def file
config=configparser.ConfigParser()
config.read("config.def")
username=config.get("OverAll", "username")
password=config.get("OverAll", "password")
#session = SessionWithHeaderRedirection(username, password)

def download(url):
    t0 = time.time()
    filename = url[url.rfind('/')+1:] 
    
    if not os.path.isfile(filename):
        print(filename)
        session = SessionWithHeaderRedirection(username, password)
        try:
          time.sleep(1)
          response = session.get(url)
          response.raise_for_status()
          f = open(filename,'wb')
          f.write(response.content)
          f.close()    
          response.close()
        except requests.exceptions.ConnectionError:
          try:
             response.close()
             session.close()
          except:
             session.close()
             time.sleep(2)
        except:
           print('requests.get() returned an error code '+str(response.status_code))
           try:
               response.close()
               session.close()
           except:
               session.close()
               time.sleep(2)  
        session.close()

# For daily url Late 
def get_url(product, year, month, day):
    url = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/{0}.06/{1}/{2}/3B-DAY-L.MS.MRG.3IMERG.{1}{2}{3}-S000000-E235959.V06.nc4".format(product,year, month,day)
    return url

def get_index(year, month, day):
    d0 = date(year, 1, 1)
    d1 = date(year, month, day)
    num1 = (d1 - d0).days + 1
    D1 = {"year": year, "month" : month,"day" : day,"num" : str((d1 - d0).days + 1).zfill(3)}
    d2 = d1 + timedelta(days=1)
    if d2.year != year:
        num2 = 1
    else:
        num2 = (d2 - d0).days + 1
    D2 = {"year": d2.year, "month" : d2.month,"day" : d2.day, "num" : str(num2).zfill(3)}
    return  D1, D2

def get_HH_urls_day(year, month, day):
    D1, D2 = get_index(year, month, day)
    # 
    A = np.arange(720,1440,30)
    
    L1 = [["{0}{1:02}00".format(12+i//2, 30*(i%2)), "{0}{1:02}59".format(12+i//2, 29+30*(i%2))] for i in range(len(A))]
    
    B = np.arange(0,720,30)
    L2 = [["{0:02}{1:02}00".format(i//2, 30*(i%2)), "{0:02}{1:02}59".format(i//2, 29+30*(i%2))] for i in range(len(B))]

    basic_url = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHHL.06/{0}/{1}/3B-HHR-L.MS.MRG.3IMERG.{0}{2:02}{6:02}-S{4}-E{5}.{3:04}.V06B.HDF5"
    L = [basic_url.format(D1["year"], D1["num"], D1["month"], a, b[0],b[1],D1["day"]) for a,b in zip(A, L1)]
    L = L + [basic_url.format(D2["year"], D2["num"], D2["month"], a, b[0],b[1],D2["day"]) for a,b in zip(B, L2) ]
    return L

def remove_thing(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def empty_directory(path):
    for i in glob.glob(os.path.join(path, '*')):
        remove_thing(i)

