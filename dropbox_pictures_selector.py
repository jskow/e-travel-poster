#!/usr/local/bin/python
"""
  Dropbox_pictures_selector.py
  Select pictures from Dropbox account.
  Based on input, rotate through pictures close to location.
  Josh Skow, January 2018.
"""

from __future__ import print_function

import argparse
import sys
import six
import dropbox
#To check for files on local system
import os.path
#Show images on the local system
from PIL import Image
#Create a delay between showing pictures
import time
#Open viewer for images
import subprocess
#Kill viewer process
import signal
#import a random number
import random
#Use to determine where you clicked on a map
import cv2
#Use to calculate long/latitude
import fractions
#Download photos and display them in parallel
import threading


#arguments to main function
parser = argparse.ArgumentParser(description="Display nearby photos")
parser.add_argument('folder', nargs='?', default='Photos',
                    help='Folder name in your Dropbox')

TOKEN=
dl_path=
#How long to display each picture
TIME_PER_PHOTO=6
debug=True
#list of points where user clicked
refPt = []
#Global flag to see if user selected a point on the map
clicked = False

#authenticate dropbox token

#Get token and local dl_path
def get_vars():
    #Open file with variables

    #Import to local variables

#get nearby photos
def get_nearby_photos(nearby_photos, res, dbx, user_long, user_lat):
    i = 0
    photo_num = 0
    #Print the first 20 entries in the folder
    #TBD: Switch to variable lat/long

    #Bay area
    cur_lat = 37.36
    cur_long = -121.98

    #Raleigh
    #cur_lat = 35.76
    #cur_long = -78.75

    #NYC
    #cur_lat = 40.75
    #cur_long = -73.98

    while (res.has_more == True):
        for entry in res.entries:
            i = i + 1

            #If there is no media info, there there is no picture

            try:
                if (entry._media_info_present == False):
                    #print('Media info present?')
                    continue
                else:
                    lat_media = entry.media_info
            except AttributeError:
                continue

            try:
                if (lat_media.is_metadata() == True):
                    photo_data = lat_media.get_metadata()
                    if (photo_data._location_present != True):
                        continue
                else:
                    continue
            except AttributeError:
                continue

            #print('Dir: ', dir(photo_data))
            #print('Entry name is', entry.name)
            #print('Lat: ', photo_data.location.latitude, 'Long: ', photo_data.location.longitude)
            photo_lat = photo_data.location.latitude
            photo_long = photo_data.location.longitude

            #Compare photos location with desired location
            if (check_nearby_loc(photo_lat, photo_long, cur_lat, cur_long)):
                if (debug == True): print('Name: ', entry.name, 'Path: ', entry.path_lower)

                #If photo is nearby, store its name in an indexed array
                #We will use random index to access to display the photos
                nearby_photos[photo_num] = entry.name
                photo_num = photo_num + 1

                #download the file that is close if not already downloaded
                if (file_not_downloaded(entry.name)):
                    try:
                        dbx.files_download_to_file(dl_path+entry.name, entry.path_lower)
                    except dropbox.exceptions.HttpError as err:
                        print('*** Http error', err)
                #else:
                    #Spawn a viewing process for the photo
                    #display_photo_mac(dl_path+entry.name)


                #print('Dir: ', dir(res), 'Type: ', type(res))
            #else:
                #print('Nope')
        print('Dir: ', dir(res.cursor), 'Value: ', res.cursor)
        res = dbx.files_list_folder_continue(res.cursor)

#check if photo nearby
def check_nearby_loc(photo_lat, photo_long, cur_lat, cur_long):
    if ((photo_lat < cur_lat + 0.3) and (photo_lat > cur_lat - 0.3)):
        if ((photo_lat < cur_lat + 0.3) and (photo_lat > cur_lat - 0.3)):
            #print('Photo is close enough!')
            return True
        else:
            return False
    else:
        return False

#Check if the photo was already downloaded
def file_not_downloaded(file_name):
    if (debug == True): ('File name: ', dl_path+file_name)
    if (os.path.isfile(dl_path+file_name)):
        if (debug == True): print('File exists already')
        return False
    else:
        if (debug == True): ('File doesn''t exist locally')
        return True

#Display photo on MacOS
def display_photo_mac(file_name):
    #Spawn a viewing process for the photo
    viewer = subprocess.call(['/usr/bin/open', '/Applications/Preview.app', file_name])
    time.sleep(TIME_PER_PHOTO)
    #Get the PID of the preview process
    process = subprocess.Popen('pgrep Preview', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    my_pid, err = process.communicate()

    #Kill PID of open viewer process
    #sometimes PID is not found, just ignore it
    try:
        os.kill(int(my_pid), signal.SIGKILL)
    except ValueError:
        return

#output photo from index array
def print_random_photo(nearby_photos):
    #If there are no photos yet, don't try to print anything
    i = 0
    while (i < 500):
        i = i + 1
        #Could take a while to download/find some relevant photos
        if (len(nearby_photos) == 0):
            print('Waiting for photo...')
            time.sleep(5)
            continue
        #Seed random
        random_num = random.random()
        #Get photo at random index
        random_num = round(random_num * len(nearby_photos))
        #display photo
        #Somtimes the photo isn't found in the dictionary, so
        #just try again to find another photo
        try:
            display_photo_mac(dl_path + nearby_photos[random_num])
        except KeyError:
            continue

#Detect coordinates to show photos nearby on a map
#This is a callback to OpenCV to record mouse clicks
def get_coordinates_from_user(event, x, y, flags, param):
    global refPt
    global clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        #print('X Coord: ', x, 'Y coord: ', y)
        clicked = True

#show a map of the USA to the user
def display_map_of_usa():
    global clicked
    usa_image = cv2.imread('/Users/jskow/Programming/interactive-poster/new-map-of-usa.jpg', 1)
    #Resize image to a reasonable size for the user
    out_img = cv2.resize(usa_image, (0,0), fx=0.9, fy=0.9)

    cv2.namedWindow("Map of USA")
    cv2.setMouseCallback("Map of USA", get_coordinates_from_user)

    while True:
        cv2.imshow("Map of USA", out_img)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif clicked == True:
            break

    #Scale xy click based on size of current image
    #print('Type: ', type(refPt[0]))
    #print('Dir: ', dir(out_img), 'Type: ', type(out_img))
    img_dimensions = out_img.shape
    #print('Dir: ', dir(img_dimensions), 'Type: ', type(img_dimensions))
    #print('Width:', img_dimensions[1], 'Height:', img_dimensions[0])
    new_long, new_lat = convert_xy_to_gps(refPt[0][0], refPt[0][1], img_dimensions[1], img_dimensions[0])
    cv2.destroyAllWindows()
    return (new_long, new_lat)

#Convert the x,y coordintates to GPS coordinates
def convert_xy_to_gps(x, y, width, height):
    #print('X: ', x, 'Y:', y, 'Width:', width, 'Height:', height)
    #approx max/min values for USA
    #Based on portion of USA shown in the picture
    #Because the map has parts of ocean, so we need to
    #take that into account to calculate where the user clicked
    max_lat = 49.67
    min_lat = 23.24
    max_long = -128.66
    min_long = -63.01

    #y/height represents the % across the picture clicked
    #Max latitude - min latitude is the delta latitude possible
    #By multiplying the % times the delta, we know how far across
    #the pictures we should be, so we add that to the minimum value.

    #Python requires casting floats on division
    percent_x = float(x)/float(width)
    #Largest negative value when x=0, so subtract the large negative
    #delta to show a point on the far right side of the map
    approx_long = max_long - ((percent_x)*(max_long-min_long))
    #OpenCV y value is 0 at the top, 100 at the bottom
    #So we need to subtract % from the top
    percent_y = float(y)/float(height)
    approx_lat = max_lat - ((percent_y)*(max_lat-min_lat))
    #print('Latitude: ', approx_lat, 'Longitude:', approx_long)
    return (approx_long, approx_lat)


#Arguments - Location to find nearby photos
#main function
#1. authenticate dropbox token
#2. go to photos folder
#3. make index array of photos within 100m of Location
#4. output one photo from array randomly every 5s
def main():
    args = parser.parse_args()

    folder = args.folder
    #print('Dropbox folder name:', folder)

    #open dropbox object
    dbx = dropbox.Dropbox(TOKEN, user_agent="PictureSelector")

    #Show user a map, allow them to select coordinates
    #This returns coordinates converted from selection on the map
    user_long, user_lat = display_map_of_usa()
    print('Latitude:', user_lat, 'Longitude: ', user_long)

    #This is the default Dropbox Photo upload folder
    path = '/Camera Uploads'
    try:
        res = dbx.files_list_folder(path, include_media_info=True, limit=20)
    except dropbox.exceptions.ApiError as err:
        print('Failure getting folder for', path)
        return {}
    else:
        start = time.time()
        nearby_photos = {}
        #We want to get photos, and display photos in parallel
        print('prepare to create thread')
        #try:
        get_photos_thread = threading.Thread(target=get_nearby_photos,
                                args=(nearby_photos, res, dbx, user_long, user_lat))
        #This allows program to kill threads when main thread is killed
        #Basically, allow me to use ctrl+C
        get_photos_thread.daemon = True

        print('create get photos thread')
        #Single tuple required to successfully pass the argument
        print_photos_thread = threading.Thread(target=print_random_photo,
                                args=(nearby_photos,))
        print_photos_thread.daemon = True

        print('create print photos thread')
        get_photos_thread.start()
        print_photos_thread.start()

        #get_photos_thread.join()
        while True:
            time.sleep(1)
        end = time.time()
        print('Length: ', len(nearby_photos), 'Execution time: ', end - start)
        for i in range(1,len(nearby_photos)):
            print_random_photo(nearby_photos)



##Main program code
main()
