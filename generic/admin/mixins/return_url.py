from django import http
from django.contrib import admin

class ReturnURLAdminMixin(admin.ModelAdmin):
    def response_add(self, request, obj, *args, **kwargs):
        referrer = request.GET.get('_return_url')
        if referrer and not '_continue' in request.POST:
            return http.HttpResponseRedirect(referrer)
        else:
            return super(ReturnURLAdminMixin, self).response_add(
                request, obj, *args, **kwargs)

    def response_change(self, request, obj):
        referrer = request.GET.get('_return_url')
        if (referrer and
            not '_continue' in request.GET and
            not '_popup' in request.GET and
            not '_continue' in request.POST and
            not '_popup' in request.POST
        ):
            return http.HttpResponseRedirect(referrer)
        else:
            return super(ReturnURLAdminMixin, self).response_change(
                request, obj)
