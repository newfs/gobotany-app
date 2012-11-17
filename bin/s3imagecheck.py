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
url_pattern = re.compile(r'/taxon-images/[A-Z]')

def main():

    conn = boto.connect_s3()
    bucket = conn.get_bucket('newfs')
    ls_taxon_images_gz = bucket.get_key('ls-taxon-images.gz').read()

    directory_count = 0
    image_count = 0
    error_count = 0
    bad_header_count = 0

    hostname = 'newfs.s3.amazonaws.com'
    ip = socket.gethostbyname(hostname)
    session = requests.Session()

    t0 = time.time()
    g = gzip.GzipFile(fileobj=StringIO(ls_taxon_images_gz))
    for line in g:
        # if image_count > 100:
        #     break  # limit running time, for debugging
        fields = line.split()
        url = fields[3]
        if not url_pattern.search(url):
            continue
        path = url.replace('s3://newfs', '')
        url = 'http://{}{}'.format(ip, path)
        headers = {'Host': hostname}
        if url.endswith('/'):
            directory_count += 1
            expected_code = 403
        else:
            image_count += 1
            expected_code = 200

        response = session.head(url, headers=headers)
        if response.status_code != expected_code:
            print 'Error: {} -> {}'.format(url, response.status_code)
            error_count += 1
            if response.status_code == 200:
                print '       Making resource private'
                key = bucket.get_key(path)
                key.set_acl('private')
            elif response.status_code == 403:
                print '       Making resource public'
                key = bucket.get_key(path)
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
