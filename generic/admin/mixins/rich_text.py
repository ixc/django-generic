from django.conf import settings
from django.contrib import admin

def make_rich(base):
    BaseMedia = getattr(base, 'Media', object)

    class BaseRichTextModelAdmin(base):
        rich_fields = ()

        class Media(BaseMedia):
            js = tuple(getattr(BaseMedia, 'js', ())) + (
                settings.TINYMCE_JS_URL,
                settings.TINYMCE_JS_INIT_URL,
            )

        def formfield_for_dbfield(self, db_field, **kwargs):
            formfield = super(
                BaseRichTextModelAdmin, self
            ).formfield_for_dbfield(db_field, **kwargs)
            if db_field.name in self.rich_fields:
                formfield.widget.attrs.update({'class': 'rich-text'})
            return formfield
    return BaseRichTextModelAdmin


RichTextModelAdmin = make_rich(admin.ModelAdmin)
RichTextStackedInline = make_rich(admin.StackedInline)
RichTextTabularInline = make_rich(admin.TabularInline)

