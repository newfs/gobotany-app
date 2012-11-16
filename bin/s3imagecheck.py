#!/usr/bin/env python

"""S3 image permission scanner

Determine whether our S3 images listed in ls-taxon-images.gz all have
the correct permissions when accessed publicly: no directories should
allow themselves to be listed, while all images and thumbnails should
allow themselves to be downloaded.

"""
import gzip
import re
import requests
import socket
import time

url_pattern = re.compile(r'/taxon-images/[A-Z]')

def main():
    directory_count = 0
    image_count = 0
    error_count = 0

    hostname = 'newfs.s3.amazonaws.com'
    ip = socket.gethostbyname(hostname)
    session = requests.Session()

    g = gzip.GzipFile('ls-taxon-images.gz')
    t0 = time.time()
    for line in g:
        if image_count > 100:
            break
        fields = line.split()
        url = fields[3]
        if not url_pattern.search(url):
            continue
        url = url.replace('s3://newfs/', 'http://{}/'.format(ip))
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

    elapsed = time.time() - t0
    per_second = (directory_count + image_count) / elapsed

    print 'Scanned {} directories'.format(directory_count)
    print 'Scanned {} images'.format(image_count)
    print 'Scanned {:.2} resources per second'.format(per_second)
    print 'Found {} errors'.format(error_count)

if __name__ == '__main__':
    main()
