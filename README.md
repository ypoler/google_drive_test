# google_drive_test
google API tests

This small demo is based on the google drive API demo. 

Its purpose is to run every X hours or logon, connect to the drive and sample some photos ("photos" is a designated space - another version mapped the hierarchy of the entire folders under the "google photos" folder).

The photos are downloaded to a local directory (folder called "pictures" which is a child of the code's folder) and can be used as wallpaper slideshow, etc.

I couldn't find a proper way to mark the faviourites photos and later extract them - appearntly photos cannot be starred, and adding some tag to their description isn't read in the google API.
Therefore, the sample is from ALL photos.

The demo is using the oAuth2 authentication mechanism. In order to authenticate the application, one needs to follow the instructions as shown in https://developers.google.com/drive/v3/web/quickstart/python#step_1_turn_on_the_api_name

It also require python (I've used 2.7) and the google API package, all preperation instructions are listed in https://developers.google.com/drive/v3/web/quickstart/python

The main has 2 extra parameters (which aren't related to oAuth):
* num_samples: number of pictures to sample (default = 15)
* delete_old: if set, will remove all files in the pictures directory
