web: newrelic-admin run-program gunicorn -b "0.0.0.0:$PORT" -w 3 gobotany.wsgi:application
s3imagecheck: bin/s3imagecheck.py
s3imagescan: bin/s3imagescan.sh
s3thumbnail: bin/s3thumbnail.sh
nightly: bin/email-wrap.py bin/nightly.sh
