from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import NoArgsCommand

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

        # Get all the images which are either already approved, or not yet screened
        # Exclude any images that are either already deleted or orphaned
        active_images = ScreenedImage.objects.exclude(deleted=True).exclude(
                orphaned=True).exclude(is_approved=False, screened__isnull=False)
        active_files = []
        active_thumbs = []
        for image in active_images:
            active_files.append(image.image.url)
            active_thumbs.append(image.thumb.url)

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
            self.stdout.write('{0}\n'.format([image.image.url for image in stale_images]))

        # Make really REALLY sure we're not deleting something we shouldn't
        for stale_image in stale_images:
            conflict_image = stale_image.image.url in active_files
            conflict_thumb = stale_image.thumb.url in active_thumbs
            if conflict_image or conflict_thumb:
                conflict_msg = 'CONFLICT: Stale file at {0} (thumb: {1}) matches an active file. Skipping deletion.\n'.format(stale_image.image.url, stale_image.thumb.url)
                self.stdout.write(conflict_msg)
            else:
                if verbosity >= '3':
                    self.stdout.write('Deleting image: {0}\n'.format(stale_image.image.url))
                    self.stdout.write('Deleting thumbnail: {0}\n'.format(stale_image.thumb.url))
                if not dry_run:
                    try:
                        stale_image.image.storage.delete(stale_image.image.name)
                    except IOError as e:
                        self.stdout.write('IOError while attempting to delete image: {0}'.format(
                            stale_image.image.name))
                    try:
                        stale_image.thumb.storage.delete(stale_image.thumb.name)
                    except IOError as e:
                        self.stdout.write('IOError while attempting to delete thumb: {0}'.format(
                            stale_image.thumb.name))

                    try:
                        stale_image.deleted = True
                        stale_image.save()
                    except:
                        self.stdout.write('WARNING: Failed to flag ScreenedImage as deleted.')


        if verbosity >= '1':
            self.stdout.write('Cleanup complete.\n')
        
