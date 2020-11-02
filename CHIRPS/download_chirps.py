"""
Download the full CHIRPS 2.0 data for a specific type (dekads, pentads, daily ...)
with the possibility to automatically recut the data over Argentina.
"""
import os
import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import subprocess

##############

# PARAMETERS to define

# Set a pre-existing directory where the CHIRPS files must be saved
download_dir  = ""
# Url for global dekad, change if you want another product
url = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_dekad/netcdf/'
# Recut the data over Argentina
argentina = False

##############
if download_dir != "":
    os.chdir(download_dir)

    response = requests.get(url)
    soup = BeautifulSoup(response.text,"html.parser")
    soup.findAll('a')
    
    # First link to download in the page
    # Here the index = 5 is valid for the dekad link but it may change if you download another product (ex : daily, dekad, monthly)
    # To be sure you can check the link and check that it is the first year
    one_a_tag = soup.findAll('a')[5:] 
    links = [one_a_tag[i]['href'] for i in range(len(one_a_tag))]

    for link in links:
        print(link)
        download_url = url + link
        urllib.request.urlretrieve(download_url,"./"+link)
        # Section to recut CHIRPS over Argentina
        if argentina:
            subprocess.check_call(["cdo", "sellonlatbox,-80,-44,-60,-20", link, link.replace(".nc", "ARG.nc")])
            subprocess.check_call(["rm", link])
        time.sleep(1)

else:
    print("Please enter a valid download direction")
    
