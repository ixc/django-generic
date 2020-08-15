from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Set Site name and domain from settings.SITE_NAME/DOMAIN'
    def handle(self, *args, **options):
        if not 'django.contrib.sites' in settings.INSTALLED_APPS:
            raise CommandError('Not applicable if Sites is not installed')
        try:
            site = Site.objects.get(id=settings.SITE_ID)
        except Site.DoesNotExist:
            site = Site.objects.create(
                id=settings.SITE_ID,
                domain=settings.SITE_DOMAIN,
                name=settings.SITE_NAME,
            )
        except Site.MultipleObjectsReturned:
            raise # multiple sites with same ID?!
        else:
            site.domain = settings.SITE_DOMAIN
            site.name = settings.SITE_NAME
            site.save()

        if options.get('verbosity', 1) >= 1:
            self.stdout.write(
                'Site details set:\n   %s / %s\n' % (site.name, site.domain))
