import logging
logger = logging.getLogger(__name__)

class ThumbnailAdminMixin(object):
    """
    Shortcut for displaying a thumbnail in a changelist (or inline).

    Requires easy-thumbnails.

    Specify ImageField name in `thumbnail_field`, and optionally override
    `thumbnail_options` for customisation such as sizing, cropping, etc.
    Plays nicely with list_display_links if you want a clickable thumbnail.

    Add 'thumbnail' to `list_display` or `readonly_fields`, etc to display.
    """

    thumbnail_field = None
    thumbnail_options = {'size': (100,100)}

    def get_thumbnail_source(self, obj):
        if self.thumbnail_field:
            try:
                return getattr(obj, self.thumbnail_field)
            except AttributeError:
                logger.error(
                    'ThumbnailAdminMixin.thumbnail_field getattr failed')
        else:
            logger.warning('ThumbnailAdminMixin.thumbnail_field unspecified')

    def thumbnail(self, obj):
        source = self.get_thumbnail_source(obj)
        if source:
            from easy_thumbnails.files import get_thumbnailer
            thumbnailer = get_thumbnailer(source)
            try:
                try:
                    # Is thumbnail_options an alias?
                    thumbnail = thumbnailer[self.thumbnail_options]
                except KeyError:
                    # Nope! Must be an options dict.
                    thumbnail = thumbnailer.get_thumbnail(
                        self.thumbnail_options)
            except Exception:
                return ''
            return '<img class="thumbnail" src="{0}" />'.format(thumbnail.url)
        else:
            return ''
    thumbnail.allow_tags = True
