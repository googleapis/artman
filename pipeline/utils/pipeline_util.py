"""Utils related to pipeline"""

import os
import subprocess
import urlparse


def validate_exists(required, **kwargs):
    for arg in required:
        if arg not in kwargs:
            raise ValueError('{0} must be provided'.format(arg))


def download(url, directory):
    filename = os.path.basename(urlparse.urlsplit(url).path)
    if not os.path.isfile(os.path.join(directory, filename)):
        subprocess.call(['mkdir', '-p', directory])
        print 'Downloading file from URL:' + url
        subprocess.call(
            ['curl', '-o', directory + filename, '-sL', url])
    return directory + filename
