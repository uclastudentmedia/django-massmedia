from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext, loader
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db.models.fields.related import ManyToOneRel

from massmedia import settings
from massmedia.models import Image, Video, Audio, Flash, Collection,\
                             CollectionRelation, MediaTemplate

if settings.USE_VOXANT:
    from massmedia.models import VoxantVideo

class CollectionRelationForm(forms.Form):
    collection = forms.IntegerField(required=False,
        widget=ForeignKeyRawIdWidget(ManyToOneRel(Collection, Collection._meta.pk.name)))
    
    def _media(self):
        from django.conf import settings
        js = ['js/core.js', 'js/admin/RelatedObjectLookups.js']
        return forms.Media(js=['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js])
    media = property(_media)

class ContentTypeForm(forms.Form):
    ct  = forms.IntegerField(widget=forms.HiddenInput())
    ids = forms.CharField(widget=forms.HiddenInput())

class GenericCollectionInlineModelAdmin(admin.options.InlineModelAdmin):
    ct_field = "content_type"
    ct_fk_field = "object_id"
    def __init__(self, parent_model, admin_site):
        super(GenericCollectionInlineModelAdmin, self).__init__(parent_model, admin_site)
        ctypes = ContentType.objects.all().order_by('id').values_list('id', 'app_label', 'model')
        elements = ["%s: '%s/%s'" % (x, y, z) for x, y, z in ctypes]
        self.content_types = "{%s}" % ",".join(elements)
    
    def get_formset(self, request, obj=None):
        result = super(GenericCollectionInlineModelAdmin, self).get_formset(request, obj)
        result.content_types = self.content_types
        result.ct_fk_field = self.ct_fk_field
        return result

class GenericCollectionTabularInline(GenericCollectionInlineModelAdmin):
    template = 'admin/edit_inline/gen_coll_tabular.html'

class MediaAdmin(object):
    fieldsets = (
        (None, {'fields':('title','caption')}),
        ('Credit',{'fields':('author','one_off_author','credit','reproduction_allowed')}),
        ('Metadata',{'fields':('metadata','mime_type')}),
        ('Content',{'fields':('external_url','file')}),
        ('Connections',{'fields':('public','categories','sites')}),
        ('Widget',{'fields':('width','height')}),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('widget_template',)
        }),
    )
    list_display = ('title', 'author', 'mime_type', 'public', 'creation_date')
    list_filter = ('sites', 'creation_date','public')
    date_hierarchy = 'creation_date'
    search_fields = ('caption', 'file')
    
    actions = ['add_to_collection']
    
    def add_to_collection(self, request, queryset):
        """
        Adds the selected objects to the Collection selected.
        """
        ct = ContentType.objects.get_for_model(queryset.model)
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('%s?ct=%s&ids=%s' % (
                reverse('admin_massmedia_collection_add_collection_relations'),
                ct.pk, ",".join(selected)))
    add_to_collection.short_description = "Add to Collection(s)"

class ImageAdmin(MediaAdmin,admin.ModelAdmin):
    list_display = ('title','thumb','author','mime_type','metadata','public','creation_date')

class VideoAdmin(MediaAdmin,admin.ModelAdmin):
    list_display = ('title','thumb','author','mime_type','metadata','public','creation_date')
    fieldsets = MediaAdmin.fieldsets + ( ('Thumbnail',{'fields':('thumbnail',)}), )
    raw_id_fields = ('thumbnail',)

if settings.USE_VOXANT:
    class VoxantVideoAdmin(VideoAdmin):
        list_display = ('asset_id','layout_id') + VideoAdmin.list_display
        fieldsets = ( ('Voxant',{'fields':('asset_id','layout_id')}), )
        for fieldset in VideoAdmin.fieldsets:
            if fieldset[0] == 'Content':
                continue
            fieldsets += (fieldset,)
    admin.site.register(VoxantVideo, VoxantVideoAdmin)
    
class AudioAdmin(MediaAdmin,admin.ModelAdmin): pass
class FlashAdmin(MediaAdmin,admin.ModelAdmin): pass

class CollectionInline(admin.TabularInline):
    model = CollectionRelation

class CollectionAdmin(admin.ModelAdmin):
    fields = ('title','caption','zip_file','public','categories','sites')
    list_display = ('title','caption', 'public', 'creation_date')
    list_filter = ('sites', 'creation_date','public')
    date_hierarchy = 'creation_date'
    search_fields = ('caption',)
    inlines = (CollectionInline,)
    
    class Media:
        js = ('js/genericcollections.js',)
    
    def get_urls(self):
        base_urls = super(CollectionAdmin, self).get_urls()
        custom_urls = patterns('',
            url(r'^add_collection_relations/$',
                self.admin_site.admin_view(self.add_collection_relations),
                name='admin_massmedia_collection_add_collection_relations'),
        )
        return custom_urls + base_urls
    
    def add_collection_relations(self, request):
        from django.forms.formsets import formset_factory
        from django.template.defaultfilters import capfirst, pluralize
        
        CollectionFormSet = formset_factory(CollectionRelationForm, extra=4)
        form = ContentTypeForm(request.GET)
        formset = CollectionFormSet()
        
        if request.method == "POST":
            formset = CollectionFormSet(request.POST)
            form = ContentTypeForm(request.POST)

        if form.is_valid():
            try:
                ct = ContentType.objects.get(pk=form.cleaned_data.get('ct'))
            except ContentType.DoesNotExist:
                raise Http404
        else:
            # The form is invalid, which should never happen (even on initial GET).
            # TODO: Should I raise 404 or redirect?
            raise Http404
        
        if formset.is_bound and formset.is_valid():
            ids = form.cleaned_data.get('ids').split(',')
            objects = ct.model_class()._default_manager.filter(pk__in=ids)
            num_collections = 0
            for c_form in formset.forms:
                collection_id = c_form.cleaned_data.get('collection', None)
                if collection_id is not None:
                    collection = Collection.objects.get(pk=collection_id)
                    for obj in objects:
                        cr = CollectionRelation.objects.create(content_object=obj, collection=collection)
                        collection.collectionrelation_set.add(cr)
                    num_collections += 1
            
            redir_url = '%sadmin_%s_%s_changelist' % (
                            self.admin_site.name,
                            ct.model_class()._meta.app_label,
                            ct.model_class()._meta.module_name)
            request.user.message_set.create(
                message='%s %s%s successfully added to the selected %s%s.' % (
                    len(objects),
                    capfirst(ct.model_class()._meta.verbose_name),
                    pluralize(len(objects)),
                    capfirst(Collection._meta.verbose_name),
                    pluralize(num_collections)
                    ))
            return HttpResponseRedirect(reverse(redir_url))

        t = loader.get_template('admin/massmedia/add_collection_relations.html')
        c = RequestContext(request, {
            'ct_opts':     ct.model_class()._meta,
            'collection_opts': Collection._meta,
            'formset': formset,
            'form': form,
            'media': form.media + formset.media
        })
        return HttpResponse(t.render(c))

admin.site.register(Collection , CollectionAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Audio, AudioAdmin)
admin.site.register(Flash, FlashAdmin)
admin.site.register(CollectionRelation)

if settings.TEMPLATE_MODE == settings.ADMIN:
    admin.site.register(MediaTemplate)