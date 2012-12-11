#!/usr/bin/env python

"""S3 image permission scanner

Determine whether our S3 images listed in ls-taxon-images.gz all have
the correct permissions when accessed publicly: no directories should
allow themselves to be listed, while all images and thumbnails should
allow themselves to be downloaded.  An attempt is made to fix images
with bad permissions.

"""
import gzip
import os
import re
import socket
import time
from StringIO import StringIO

import boto
import requests

CACHE_CONTROL = 'max-age=28800, public'
THUMBNAIL_DIRS = '160x149', '239x239', '1000s1000'
url_pattern = re.compile(r'/taxon-images/[A-Z]')

def generate_paths(bucket):
    ls_taxon_images_gz = bucket.get_key('ls-taxon-images.gz').read()
    g = gzip.GzipFile(fileobj=StringIO(ls_taxon_images_gz))
    for line in g:
        fields = line.split()
        url = fields[3]
        if not url_pattern.search(url):
            continue
        yield url
        for dirname in THUMBNAIL_DIRS:
            yield url.replace('/taxon-images', '/taxon-images-' + dirname)

def main():
    conn = boto.connect_s3()
    bucket = conn.get_bucket('newfs')

    directory_count = 0
    image_count = 0
    error_count = 0
    bad_header_count = 0

    hostname = 'newfs.s3.amazonaws.com'
    ip = socket.gethostbyname(hostname)
    session = requests.Session()

    t0 = time.time()
    for url in generate_paths(bucket):
        # if 'Dryopteridaceae' not in url:
        #     continue  # limit running time, for debugging
        path = url.replace('s3://newfs', '')
        url = 'http://{}{}'.format(ip, path)
        headers = {'Host': hostname}
        if url.endswith('/'):
            directory_count += 1
            expected_code = 403
        elif url.endswith('.jpg'):
            image_count += 1
            expected_code = 200
        else:
            print 'Warning: unrecognized {}'.format(url)
            continue

        response = session.head(url, headers=headers)
        if response.status_code != expected_code:
            print 'Error: {} -> {}'.format(url, response.status_code)
            error_count += 1
            key = bucket.get_key(path)
            if key is None:
                print '       Resource does not exist'
            elif response.status_code == 200:
                print '       Making resource private'
                key.set_acl('private')
            elif response.status_code == 403:
                print '       Making resource public'
                key.make_public(headers={'cache-control': CACHE_CONTROL})
            continue

        cc = response.headers.get('cache-control')
        if not url.endswith('/') and cc != CACHE_CONTROL:
            print 'Error: {} cache-control = {!r}'.format(url, cc)
            bad_header_count += 1
            continue

    elapsed = time.time() - t0
    per_second = (directory_count + image_count) / elapsed

    print 'Scanned {} directories'.format(directory_count)
    print 'Scanned {} images'.format(image_count)
    print 'Scanned {:.2f} resources per second'.format(per_second)
    print 'Found {} errors'.format(error_count)
    print 'Found {} bad headers'.format(bad_header_count)

if __name__ == '__main__':
    main()
