#!/usr/bin/env python

"""S3 image permission scanner

Determine whether our S3 images listed in ls-taxon-images.gz all have
the correct permissions when accessed publicly: no directories should
allow themselves to be listed, while all images and thumbnails should
allow themselves to be downloaded.  An attempt is made to fix images
with bad permissions.

"""
import re
import socket
import time

import boto
import requests

DEBUG = False
CACHE_CONTROL = 'max-age=28800, public'
THUMBNAIL_DIRS = '160x149', '239x239', '1000s1000'
url_pattern = re.compile(r'/taxon-images/[A-Z]')

def main():
    operator = Operator('newfs')
    family_names = operator.list_families()
    for family_name in family_names:
        if DEBUG and family_name != 'Dryopteridaceae':
            continue  # skip all but one family to speed debugging
        check_family(operator, family_name)
    operator.final_report()

def check_family(operator, family_name):
    """Check all the images and thumbnails for a family of plants.

    Families are reasonable-sized chunks of our image collection, so
    this main image-checking and thumbnail-checking routine operates on
    one family each time it is called.

    """
    images = list(operator.list_images(family_name))
    image_names = set(names_of(images))
    check_images(operator, images)

    for thumbdir in THUMBNAIL_DIRS:
        thumbs = operator.list_thumbnails(family_name, thumbdir)

        for thumb in thumbs:
            thumb_name = name_of(thumb)
            if thumb_name not in image_names:
                operator.error(thumb, 'Thumbnail is an orphan; deleting')
                thumb.delete()
                continue

def check_images(operator, keys):
    for key in keys:
        if key.name.endswith('/'):
            check_directory(operator, key)
        else:
            check_image(operator, key)

def check_directory(operator, key):
    r = operator.head(key.name)
    if r.status_code != 403:
        operator.error(key, 'Status code {} != 403 - making private'
                       .format(r.status_code))
        key.set_acl('private')

def check_image(operator, key):
    if not key.name.endswith('.jpg'):
        operator.error(key, 'Unrecognized image extension')
        return
    r = operator.head(key.name)
    if r.status_code != 200:
        operator.error(key, 'Making image public; status code was {}'
                       .format(r.status_code))
        key.make_public(headers={'cache-control': CACHE_CONTROL})
        return
    content_type = r.headers.get('content-type')
    if content_type != 'image/jpeg':
        operator.error(key, 'Bad image content-type: {}'.format(content_type))
        # Not sure what to do about this one; shouldn't it get set to
        # the correct value automatically thanks to the upload tool?
        return
    cache_control = r.headers.get('cache-control')
    if cache_control != CACHE_CONTROL:
        operator.error(key, 'Fixing bad cache-control value: {}'
                       .format(cache_control))
        key.make_public(headers={'cache-control': CACHE_CONTROL})
        return

class Operator(object):
    """Perform checks and run actions on our image database.

    This class is convenient - it is the only thing that the above code
    needs to pass around to be able to talk to our S3 bucket both over
    normal HTTP and also through boto - and it is also very efficient,
    because it holds open HTTP sessions and also caches our S3 hostname
    to avoid repeated DNS lookups.

    """
    def __init__(self, bucket_name):
        boto_connection = boto.connect_s3()
        self.bucket = boto_connection.get_bucket('newfs')

        self.t0 = time.time()
        self.directory_count = 0
        self.image_count = 0
        self.error_count = 0

        self.hostname = '{}.s3.amazonaws.com'.format(bucket_name)
        self.cached_ip = socket.gethostbyname(self.hostname)
        self.session = requests.Session()

    def head(self, path):
        if not path.startswith('/'):
            path = '/' + path
        if path.endswith('/'):
            self.directory_count += 1
        else:
            self.image_count += 1
        url = 'http://{}{}'.format(self.cached_ip, path)
        headers = {'Host': self.hostname}
        response = self.session.head(url, headers=headers)
        return response

    def list_families(self):
        seq = self.bucket.list('taxon-images/', '/')
        return names_of(seq)

    def list_images(self, family_name):
        seq = self.bucket.list('taxon-images/{}/'.format(family_name))
        return seq

    def list_thumbnails(self, family_name, thumbdir):
        dirname = 'taxon-images-{}/{}/'.format(thumbdir, family_name)
        seq = self.bucket.list(dirname)
        return seq

    def error(self, key, message):
        print key.name
        print ' ', message
        self.error_count += 1

    def final_report(self):
        elapsed = time.time() - self.t0
        per_second = (self.directory_count + self.image_count) / elapsed
        print
        print 'Scan took {:.2f} seconds'.format(elapsed)
        print 'Scanned {:.2f} resources per second'.format(per_second)
        print 'Scanned {} directories'.format(self.directory_count)
        print 'Scanned {} images'.format(self.image_count)
        print 'Found {} errors'.format(self.error_count)

def name_of(key):
    return key.name.rstrip('/').split('/')[-1]

def names_of(keys):
    for key in keys:
        yield name_of(key)

if __name__ == '__main__':
    main()
