##################################################
#
#   This demo is based on google's drive API example.
#
#
#   Its purpose is to:
#   1. get all image files sorted by createdTime from "google photos" folder
#   2. sample from the list some IDs
#   3. If required, delete current pictures from the designated directory
#   4. Download the sampled photos into the pictures directory  
#
#   references:
#   https://developers.google.com/drive/v3/web/quickstart/python - google API python intro
#   https://developers.google.com/drive/v3/web/search-parameters - search files
#   https://developers.google.com/drive/v3/reference/files/list
#   https://developers.google.com/drive/v3/reference/files/get
#   https://developers.google.com/drive/v3/web/manage-downloads - download files
#
#   Note that in order to revoke the oAUth permissions, need to delete the JSON copy in ~/.credentials -
#   if not, it stays there with the old credentials
#
#
##################################################



from __future__ import print_function
import httplib2
import os
import io
import sys  
reload(sys)  
sys.setdefaultencoding('utf-8')
import glob
import random
import shutil
import argparse


from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument('--target_dir', dest='target_dir', default="./pictures",
                    help='folder to place te pictures in')
    parser.add_argument('--num_samples', dest='num_samples', type=int, default=15,
                    help='Number of samples to take from the full image list')
    parser.add_argument('--delete_old', dest='delete_old', action='store_true', default='False',
                    help='If set, delete the content of the current pictures directory')					
    args = parser.parse_args()

except ImportError:
    parser = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if args:
            credentials = tools.run_flow(flow, store, args)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

	
def add_files_results_id_name(files_service, query):
    """
	Run a query which yields id + name and return all those file tuples as array
	"""
    file_arr = []
    page_token = None
    while (True):
        results = files_service.list(q=query,
            fields="nextPageToken, files(id, name)",
            orderBy="createdTime",
			spaces="drive",
            pageToken=page_token).execute()
        items = results.get('files', [])
        if not items:
            break;
        else:
            for item in items:
                tup = (item['name'], item['id'])
                file_arr.append(tup)
            page_token = results.get('nextPageToken', None)
            if (page_token is None):
                break;
    return file_arr				

				
def get_google_photos_filelist(files_service):
    """
    Query google photos directory (hierarchical per year)
    """

    # First, get the root "Google photos" directory
    query_str = "mimeType='application/vnd.google-apps.folder' and name = 'Google Photos'"
    photos_dir = add_files_results_id_name(files_service, query_str)
    _, photos_dir_id = photos_dir[0]

    # Next, bring its children (one directory per year)
    query_str = "mimeType='application/vnd.google-apps.folder' and parents in '" + photos_dir_id + "'"
    photos_subdirs = add_files_results_id_name(files_service, query_str)

    # Finally, concat all children IDs to the query and search the Images
    query_str = "mimeType contains 'image/' and parents in '" + "', '".join(photos_dir_id for _, photos_dir_id in photos_subdirs) + "'"
    pictures_list = add_files_results_id_name(files_service, query_str)
    return pictures_list


def download_file(files_service, file_id, filename):
    """
	Download a binary file given its ID into full-path filename
    """
    request = files_service.get_media(fileId=file_id)
    fh = io.FileIO(filename.strip(), 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

		
def sample_pictures_from_list(full_list, num):
    """
	Sample several files from the full_list
	"""
    random.seed()
    sample_pics = random.sample( full_list, num )
    return sample_pics


def download_pictures_to_dir(files_service, picture_list, base_dir):
    cnt_files = 0
	
    """
    Create base_dir (if doesn't exist yet)
    """
    if os.path.exists(base_dir) == False:
        os.mkdir(base_dir)
	   
    """
	Download files from the pictures list into the base_dir.
	In case of exception, continue to the next sample
    """	   
    for pic in picture_list:
        name = pic[0]
        id = pic[1]
        filename = base_dir + "\\" + name
        try:
            download_file(files_service, id, filename)
            print("Downloaded file: " + name)
            cnt_files = cnt_files+1
        except Exception as e:
            if hasattr(e, 'message'):
                print('Failed to download {0}. Exception: {1}'.format(filename, e.message))
            else:
                print('Failed to download {0}. Exception: {1}'.format(filename, e))
#            if (os.path.exists(filename) == True): os.remove(filename)

    return cnt_files
			

def remove_files_from_dir(base_dir):
	old_files = glob.glob(base_dir + "\*");
	for file in old_files:
		os.remove(file)
		
			
def main():
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    try:
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)
        print("Connected to Google services...")

        pictures_list = get_google_photos_filelist( service.files() )
        print('Found {0} files in photos'.format(len(pictures_list)) )

        sample_pics = sample_pictures_from_list(pictures_list, args.num_samples)
        print('Sampled {0} files from photos'.format(len(sample_pics)) )

        base_folder = args.target_dir #os.getcwd() + "\\pictures"
        if (args.delete_old == True):
            remove_files_from_dir(base_folder)
            print('Removed old files from {0}'.format(base_folder))

        num_downloaded_files = download_pictures_to_dir( service.files(), sample_pics, base_folder )
        print('Downloaded {0} files to {1}'.format(num_downloaded_files, base_folder) )

    except Exception as e:
        if hasattr(e, 'message'):
            print('Exception: {0}'.format(e.message))
        else:
            print('Exception: {0}'.format(e))
        raw_input("Press Enter to continue...")		# wait for keypress to close the windows
			
		
if __name__ == '__main__':
    main()