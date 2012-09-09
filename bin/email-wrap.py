#!/usr/bin/env python
#
# To run a script on Heroku such that our admins get emailed its output
# (this is useful for daily automated scripts, for example) first add
# the SendGrid Heroku add-on to your application:
#
#      heroku addons:add sendgrid:starter
#
# Then set the environment variable $MAIL_TO:
#
#      heroku config:set MAIL_TO=sid@newfs.org,bill@newfs.org
#
# Finally, put the name of this script at the front of any command line:
#
#     bin/email-wrap.py bin/nightly.sh (or whatever)
#
# The result is that the command's output, both stdout and stderr, will
# be collected and then emailed to your list of email addresses.

import os
import smtplib
import subprocess
import sys

if __name__ == '__main__':
    mail_to = os.environ.get('MAIL_TO', None)
    if mail_to is None or not mail_to.strip():
        print >>sys.stderr, 'Error: set MAIL_TO before calling email-wrap.py'

    p = subprocess.Popen(
        sys.argv[1:],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        )
    (output, ignored) = p.communicate()

    fromaddr = 'no-reply@newenglandwild.org'
    toaddrs = os.environ['MAIL_TO'].replace(',', ' ').split()
    message = '\r\n'.join((
            'To: {}'.format(', '.join(toaddrs)),
            'From: {}'.format(fromaddr),
            'Subject: Heroku script output',
            '',
            output.replace('\n', '\r\n')))

    server = smtplib.SMTP('smtp.sendgrid.net', 587, 'heroku.com')
    # server.set_debuglevel(1)
    server.login(os.environ['SENDGRID_USERNAME'],
                 os.environ['SENDGRID_PASSWORD'])
    server.sendmail(fromaddr, toaddrs, message)
    server.quit()
