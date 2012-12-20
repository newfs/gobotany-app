from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import NoArgsCommand, CommandError
from django.db.models import Q

from gobotany.plantshare.models import ScreenedImage

class Command(NoArgsCommand):
    help = 'Delete user uploaded images that have been rejected or orphaned.'
    option_list = NoArgsCommand.option_list + (
        make_option('--min-age',
            type='int',
            dest='days_old',
            default=7,
            help='Minimum age of the file (in days) to be considered for deletion. Defaults to %default days.'),
        make_option('--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do a dry run. Report what would be deleted, but make no deletions or changes.'),
        )

    def handle_noargs(self, **options):
        days_old = options['days_old']
        dry_run = options['dry_run']
        verbosity = options['verbosity']
        if verbosity >= '1':
            self.stdout.write('Removing rejected or orphaned images uploaded more than {0} days ago.\n'.format(
                days_old))

        from django.conf import settings

        # Get all the images which are either already approved, or not yet screened
        active_images = ScreenedImage.objects.exclude(is_approved=False, screened__isnull=False)
        active_files = []
        active_thumbs = []
        for image in active_images:
            active_files.append(image.image.path)
            active_thumbs.append(image.thumb.path)

        if verbosity >= '3':
            self.stdout.write('Active Images:\n{0}\n'.format(active_files)) 
            self.stdout.write('Active Thumbs:\n{0}\n'.format(active_thumbs)) 
        
        # Images that have been screened and rejected, and are older than user
        # specified cutoff
        upload_cutoff = datetime.now() - timedelta(days=days_old)
        rejected_images = ScreenedImage.objects.filter(is_approved=False,
                deleted=False, screened__isnull=False,
                uploaded__lt=upload_cutoff)

        orphaned_images = ScreenedImage.objects.filter(deleted=False, 
                orphaned=True, uploaded__lt=upload_cutoff)

        stale_images = rejected_images | orphaned_images

        if verbosity >= '1':
            self.stdout.write('Found {0} images to delete.\n'.format(len(stale_images)))

        if verbosity >= '3':
            self.stdout.write('{0}\n'.format([image.image.path for image in stale_images]))

        # Make really REALLY sure we're not deleting something we shouldn't
        for stale_image in stale_images:
            if stale_image.image.path in active_files or stale_image.thumb.path in active_thumbs:
                self.stdout.write('CONFLICT: Stale file at {0} matches active file at {1}.  Skipping deletion.\n')
            else:
                if verbosity >= '3':
                    self.stdout.write('Deleting image: {0}\n'.format(stale_image.image.path))
                    self.stdout.write('Deleting thumbnail: {0}\n'.format(stale_image.thumb.path))
                if not dry_run:
                    stale_image.image.storage.delete(stale_image.image.name)
                    stale_image.thumb.storage.delete(stale_image.thumb.name)
                    stale_image.deleted = True
                    stale_image.save()

        if verbosity >= '1':
            self.stdout.write('Cleanup complete.\n')
        
