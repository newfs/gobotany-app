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

url_pattern = re.compile(r'/taxon-images/[A-Z]')

def main():
    directory_count = 0
    image_count = 0

    hostname = 'newfs.s3.amazonaws.com'
    ip = socket.gethostbyname(hostname)

    g = gzip.GzipFile('ls-taxon-images.gz')
    for line in g:
        if image_count > 10:
            break
        fields = line.split()
        url = fields[3]
        if not url_pattern.search(url):
            continue
        url = url.replace('s3://newfs/', 'http://{}/'.format(ip))
        headers = {'Host': hostname}
        print url
        if url.endswith('/'):
            directory_count += 1
            print requests.head(url, headers=headers)
        else:
            image_count += 1
            print requests.head(url, headers=headers)

    print 'Scanned {} directories'.format(directory_count)
    print 'Scanned {} images'.format(image_count)

if __name__ == '__main__':
    main()
