from django.conf import settings
from django.contrib import messages
from django.forms.models import modelform_factory
from django.forms.widgets import (TextInput, SelectDateWidget,
                                  CheckboxSelectMultiple, HiddenInput)
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls.base import reverse
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.list import ListView
from rest_framework import viewsets

from writlarge.main.mixins import (
    LearningSiteParamMixin, LearningSiteRelatedMixin,
    ModelFormWidgetMixin, LoggedInEditorMixin)
from writlarge.main.models import (
    LearningSite, ArchivalRepository, Place,
    DigitalObject, ArchivalCollection, Footnote)
from writlarge.main.serializers import (
    ArchivalRepositorySerializer, LearningSiteSerializer, PlaceSerializer)


# returns important setting information for all web pages.
def django_settings(request):
    whitelist = ['GOOGLE_MAP_API']
    return {
        'is_editor': (request.user.groups and
                      request.user.groups.filter(name='Editor').exists()),
        'settings': dict([(k, getattr(settings, k, None))
                          for k in whitelist])}


class CoverView(TemplateView):
    template_name = "main/cover.html"


class MapView(TemplateView):
    template_name = "main/map.html"


class SearchView(TemplateView):
    template_name = "main/search.html"


class PlaceDetailView(DetailView):
    model = Place


class PlaceUpdateView(LoggedInEditorMixin, ModelFormWidgetMixin, UpdateView):
    model = Place
    fields = ['title', 'notes']
    widgets = {
        'title': TextInput
    }


class LearningSiteDetailView(DetailView):
    model = LearningSite


class LearningSiteUpdateView(LoggedInEditorMixin, ModelFormWidgetMixin,
                             UpdateView):
    model = LearningSite
    fields = ['title', 'description', 'category', 'established', 'defunct',
              'instructional_level', 'founder',
              'tags', 'notes']
    widgets = {
        'title': TextInput,
        'category': CheckboxSelectMultiple,
        'established': HiddenInput,
        'defunct': HiddenInput,
        'instructional_level': TextInput
    }


class DigitalObjectCreateView(LoggedInEditorMixin,
                              ModelFormWidgetMixin,
                              LearningSiteParamMixin,
                              CreateView):
    model = DigitalObject
    fields = ['file', 'description', 'datestamp', 'source_url']
    widgets = {
        'description': TextInput,
        'datestamp': SelectDateWidget(years=range(1500, 2018))
    }

    def get_success_url(self):
        self.parent.digital_object.add(self.object)
        return reverse('site-gallery-view', args=[self.parent.id])


class DigitalObjectUpdateView(LoggedInEditorMixin,
                              ModelFormWidgetMixin,
                              LearningSiteRelatedMixin,
                              UpdateView):
    model = DigitalObject
    success_view = 'site-gallery-view'
    fields = ['file', 'description', 'datestamp', 'source_url']
    widgets = {
        'description': TextInput,
        'datestamp': SelectDateWidget(years=range(1500, 2018))
    }


class DigitalObjectDeleteView(LoggedInEditorMixin,
                              LearningSiteRelatedMixin,
                              DeleteView):
    model = DigitalObject
    success_view = 'site-gallery-view'


class LearningSiteGalleryView(LearningSiteParamMixin, ListView):
    model = DigitalObject
    template_name = 'main/learningsite_gallery.html'

    def get_queryset(self):
        return self.parent.digital_object.all()


class ArchivalCollectionLinkView(LoggedInEditorMixin,
                                 LearningSiteParamMixin,
                                 TemplateView):
    template_name = 'main/archivalcollection_link.html'

    def get_context_data(self, *args, **kwargs):
        ctx = LearningSiteParamMixin.get_context_data(self, *args, **kwargs)
        ctx['collections'] = ArchivalCollection.objects.all()
        return ctx

    def post(self, *args, **kwargs):
        collection_id = self.request.POST.get('collection', None)
        collection = get_object_or_404(ArchivalCollection, pk=collection_id)
        collection.learning_sites.add(self.parent)

        messages.add_message(
            self.request, messages.INFO,
            '{} added as an archival resource.'.format(collection)
        )

        url = reverse('site-detail-view', args=[self.parent.id])
        return HttpResponseRedirect(url)


class ArchivalCollectionUnlinkView(LoggedInEditorMixin,
                                   TemplateView):
    template_name = 'main/archivalcollection_unlink.html'

    def get_parent(self):
        parent_id = self.kwargs.get('parent', None)
        return get_object_or_404(LearningSite, pk=parent_id)

    def get_collection(self):
        pk = self.kwargs.get('pk', None)
        return get_object_or_404(ArchivalCollection, pk=pk)

    def get_context_data(self, **kwargs):
        ctx = TemplateView.get_context_data(self, **kwargs)
        ctx['parent'] = self.get_parent()
        ctx['collection'] = self.get_collection()
        return ctx

    def post(self, *args, **kwargs):
        parent = self.get_parent()
        collection = self.get_collection()
        collection.learning_sites.remove(parent)

        messages.add_message(
            self.request, messages.INFO,
            '{} removed as an archival resource.'.format(collection)
        )

        url = reverse('site-detail-view', args=[parent.id])
        return HttpResponseRedirect(url)


class ArchivalCollectionCreateView(LoggedInEditorMixin,
                                   ModelFormWidgetMixin,
                                   LearningSiteParamMixin,
                                   CreateView):
    model = ArchivalCollection
    template_name = 'main/archivalcollection_create.html'
    fields = ['repository', 'title', 'description',
              'finding_aid_url', 'linear_feet',
              'inclusive_start_date', 'inclusive_end_date']
    widgets = {
        'title': TextInput,
        'inclusive_start_date': SelectDateWidget(years=range(1500, 2018)),
        'inclusive_end_date': SelectDateWidget(years=range(1500, 2018))
    }

    repository_fields = ['title', 'latlng']
    repository_widgets = {
        'title': TextInput,
    }

    def get_context_data(self, *args, **kwargs):
        ctx = LearningSiteParamMixin.get_context_data(self, *args, **kwargs)
        ctx['repository_form'] = modelform_factory(
            ArchivalRepository, fields=self.repository_fields,
            widgets=self.repository_widgets)
        return ctx

    def get_success_url(self):
        self.object.learning_sites.add(self.parent)

        messages.add_message(
            self.request, messages.INFO,
            '{} added as an archival resource.'.format(self.object.title)
        )
        return reverse('site-detail-view', args=[self.parent.id])


class ArchivalCollectionUpdateView(LoggedInEditorMixin,
                                   ModelFormWidgetMixin,
                                   LearningSiteParamMixin,
                                   UpdateView):
    model = ArchivalCollection
    fields = ['title', 'description',
              'finding_aid_url', 'linear_feet',
              'inclusive_start_date', 'inclusive_end_date']
    widgets = {
        'title': TextInput,
        'inclusive_start_date': SelectDateWidget(years=range(1500, 2018)),
        'inclusive_end_date': SelectDateWidget(years=range(1500, 2018))
    }

    def get_success_url(self):
        messages.add_message(
            self.request, messages.INFO,
            '{} has been updated.'.format(self.object.title)
        )
        return reverse('site-detail-view', args=[self.parent.id])


class ArchivalCollectionDeleteView(LoggedInEditorMixin,
                                   LearningSiteParamMixin,
                                   DeleteView):
    model = ArchivalCollection

    def get_success_url(self):
        messages.add_message(
            self.request, messages.INFO,
            '{} has been deleted.'.format(self.object.title)
        )
        return reverse('site-detail-view', args=[self.parent.id])


class FootnoteCreateView(LoggedInEditorMixin,
                         LearningSiteParamMixin,
                         CreateView):
    model = Footnote
    fields = ['note']

    def get_success_url(self):
        self.parent.footnotes.add(self.object)
        return reverse('site-detail-view', args=[self.parent.id])


class FootnoteUpdateView(LoggedInEditorMixin,
                         LearningSiteRelatedMixin,
                         UpdateView):
    model = Footnote
    success_view = 'site-detail-view'
    fields = ['note']


class FootnoteDeleteView(LoggedInEditorMixin,
                         LearningSiteRelatedMixin,
                         DeleteView):
    model = Footnote
    success_view = 'site-detail-view'


"""
Rest API endpoints
"""


class ArchivalRepositoryViewSet(viewsets.ModelViewSet):
    queryset = ArchivalRepository.objects.all().order_by('-modified_at')
    serializer_class = ArchivalRepositorySerializer


class LearningSiteViewSet(viewsets.ModelViewSet):
    queryset = LearningSite.objects.all().order_by('-modified_at')
    serializer_class = LearningSiteSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all().order_by('-modified_at')
    serializer_class = PlaceSerializer
