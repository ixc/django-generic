from .batch import BatchUpdateForm, BatchUpdateAdmin
from .cooking import CookedIdAdmin
from .csv import CSVExportAdmin
from .delible import DelibleAdmin
from .owrt import OWRTInline, OWRTStackedInline
from .related import ChangeFormOnlyAdmin, ChangeLinkInline
from .return_url import ReturnURLAdminMixin
from .thumbnail import ThumbnailAdminMixin

try:
    from django.contrib.admin.filters import SimpleListFilter
except ImportError:
    pass # django < 1.4
else:
    from .polymorphic import PolymorphicAdmin, SubclassFilter
