# scanner settings
mode = 'demo' # 'scanner', 'read_last'
images_dir = 'bmp/'

# upload settings
user = None
password = None
upload_url = 'https://db.screenx.cz/importfile'
login_url = 'https://db.screenx.cz/accounts/login/'
status_url = 'https://db.screenx.cz/api/ajax_task_stat'

def upload(filename=None):
	pass
#     import requests
#     import os
#     import time
#     import re
#     s = requests.Session()
#     s.get(login_url)
#     login_data = {
#         'username' : user,
#         'password' : password,
#         'csrfmiddlewaretoken' : s.cookies['csrftoken']
#     }
#     r1 = s.post(login_url, login_data, headers={'Referer' : login_url})
#     data = {'upload_all': 'on', 
#             'background': 'on', 
#             'import_type': 'rack',
#            'csrfmiddlewaretoken' : s.cookies['csrftoken']}
#     files = {'thefile': (os.path.split(filename)[1], open(filename, 'rb'), 'text/csv')}
#     r4 = s.post(upload_url, data = data, files = files)
#     time.sleep(1)
#     id = re.search('async_key = "(.*)".*$', r4.text, re.MULTILINE).group(1)
#     query = {
#         'application' : 'imports',
#         'task' : 'import_files',
#         'id' : id
#     }
#     r5 = s.get(status_url, params=query)
#     print '<p>%s upload status: %s</p>' % (filename, r5.json()['status'])
