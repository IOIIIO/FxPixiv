import glob 
import os 
import math
from multiprocessing.pool import ThreadPool 

import boto3
import dataset
import pause

DB = dataset.connect('sqlite:///fxpixiv.db')
_SETTINGS = DB['settings']

CDNENDPOINT = _SETTINGS.find_one(name='cdn_endpoint')["value"]
CDNBUCKET = _SETTINGS.find_one(name='cdn_domain')["value"]
__CDNID = _SETTINGS.find_one(name='cdn_id')["value"]
__CDNKEY = _SETTINGS.find_one(name='cdn_key')["value"]
DIRECTORY = _SETTINGS.find_one(name='img_dir')["value"]

CACHE_PERCENTAGE = float(_SETTINGS.find_one(name='cdn_cache_perc')["value"])
CACHE_MIN = int(_SETTINGS.find_one(name='cdn_cache_min')["value"])
CACHE_CHUNKS = int(_SETTINGS.find_one(name='cdn_cache_chunks')["value"])

#CACHE_PERCENTAGE = 0.8
#CACHE_MIN = 1
#CACHE_CHUNKS = 3

s3_client = boto3.client('s3',
                  endpoint_url='https://' + CDNENDPOINT,
                  aws_access_key_id=__CDNID,
                  aws_secret_access_key=__CDNKEY)
 

def upload(myfile):
    s3_client.upload_file(myfile, CDNBUCKET, myfile, ExtraArgs={'ACL':'public-read'}) 
    os.remove(myfile)
    #print(myfile)

def get_files():
    batched_filenames = []
    purge_filenames = []
    raw_filenames =  sorted(glob.glob("{}/*.jpg".format(DIRECTORY)), key=os.path.getctime, reverse=True)

    total = len(raw_filenames)
    del_perc = math.ceil(total*CACHE_PERCENTAGE)

    if del_perc >= CACHE_MIN:
        purge_filenames = raw_filenames[del_perc:]
    else:
        purge_filenames = raw_filenames[CACHE_MIN:]

    for i in range(0, len(purge_filenames), CACHE_CHUNKS):
        batched_filenames.append(purge_filenames[i:i + CACHE_CHUNKS])

    return batched_filenames, len(purge_filenames)

def purge():
    filenames, total = get_files()

    pool = ThreadPool(processes=CACHE_CHUNKS*2) 
    for batch in filenames:
        pool.map(upload, batch) 
    
    return total

if __name__ == "__main__":
    while True:
        total = purge()
        print("Purged {} files".format(total))
        pause.days(4)