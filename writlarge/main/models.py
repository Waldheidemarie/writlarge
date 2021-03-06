from datetime import date

from django.contrib.auth.models import User
from django.contrib.gis.db.models.fields import PointField
from django.contrib.gis.geos.point import Point
from django.db import models
from django.db.models.aggregates import Count
from django.urls.base import reverse
from edtf import text_to_edtf
from taggit.managers import TaggableManager

from writlarge.main.utils import ExtendedDateWrapper, format_date_range


class ExtendedDateManager(models.Manager):

    def to_edtf(self, millenium, century, decade, year, month, day,
                approximate, uncertain):

        dt = ''

        if day is not None:
            dt = '{}{}{}{}-{:0>2d}-{:0>2d}'.format(
                millenium, century, decade, year, month, day)
        elif month is not None:
            dt = '{}{}{}{}-{:0>2d}'.format(
                millenium, century, decade, year, month)
        elif year is not None:
            dt = '{}{}{}{}'.format(millenium, century, decade, year)
        elif decade is not None:
            dt = '{}{}{}u'.format(millenium, century, decade)
        elif century is not None:
            dt = '{}{}uu'.format(millenium, century)
        elif millenium is not None:
            dt = '{}uuu'.format(millenium)
        else:
            return 'unknown'

        if uncertain:
            dt += '?'

        if approximate:
            dt += '~'

        return dt

    def from_dict(self, values):
        dt = self.to_edtf(
            values.get('millenium1'), values.get('century1'),
            values.get('decade1'),
            values.get('year1'), values.get('month1'),
            values.get('day1'),
            values.get('approximate1'), values.get('uncertain1'))

        if values.get('is_range'):
            dt2 = self.to_edtf(
                values.get('millenium2'), values.get('century2'),
                values.get('decade2'),
                values.get('year2'), values.get('month2'), values.get('day2'),
                values.get('approximate2'), values.get('uncertain2'))

            dt = '{}/{}'.format(dt, dt2)

        return ExtendedDate(edtf_format=dt)

    def create_from_string(self, date_str):
        edtf = str(text_to_edtf(date_str))
        return ExtendedDate.objects.create(edtf_format=edtf)


class ExtendedDate(models.Model):
    objects = ExtendedDateManager()
    edtf_format = models.CharField(max_length=256)
    lower = models.DateField(null=True)
    upper = models.DateField(null=True)

    class Meta:
        verbose_name = 'Extended Date Format'

    def _set_internal_dates(self):
        if not self.is_unknown():
            (lower, upper) = self.wrap()
            if lower:
                self.lower = lower.start_date()
            if upper:
                self.upper = upper.end_date()

    def save(self, *args, **kwargs):
        self._set_internal_dates()
        super(ExtendedDate, self).save(*args, **kwargs)

    def wrap(self):
        return ExtendedDateWrapper.create(self.edtf_format)

    def __str__(self):
        (lower, upper) = self.wrap()

        if lower and upper:
            return "%s - %s" % (lower.format(), upper.format())
        else:
            return lower.format()

    def is_unknown(self):
        return self.edtf_format == 'unknown'

    def match_string(self, date_str):
        return self.edtf_format == str(text_to_edtf(date_str))

    def to_dict(self):
        (lower, upper) = self.wrap()

        d = {}
        if lower:
            d.update(lower.to_dict(1))
        if upper:
            d.update(upper.to_dict(2))

        return d

    def get_year(self):
        # As Writ Large does not use ranges, simply return the lower year
        if self.is_unknown():
            return

        (lower, upper) = self.wrap()
        dt = lower.start_date()
        if dt and dt.year:
            return dt.year


class Footnote(models.Model):
    ordinal = models.IntegerField(default=1)
    note = models.TextField()

    def __str__(self):
        return self.note

    class Meta:
        ordering = ['ordinal']


class DigitalObject(models.Model):
    file = models.FileField(upload_to="%Y/%m/%d/", null=True, blank=True)
    source_url = models.URLField(null=True, blank=True)

    description = models.TextField()
    date_taken = models.ForeignKey(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='Date Taken')
    datestamp = models.DateField(
        null=True, blank=True, verbose_name='Date Taken')
    source = models.TextField(
        null=True, blank=True,
        help_text="Where did you find this photo?")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Digital Object"
        ordering = ['-created_at']

    def __str__(self):
        return self.description

    def get_url(self):
        if self.file:
            return self.file.url
        else:
            return self.source_url


class LearningSiteCategory(models.Model):
    name = models.TextField(unique=True)
    group = models.TextField(default='other')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class InstructionalLevel(models.Model):
    name = models.TextField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Audience(models.Model):
    name = models.TextField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ArchivalRecordFormat(models.Model):
    name = models.TextField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PlaceManager(models.Manager):

    def __init__(self, fields=None, *args, **kwargs):
        super(PlaceManager, self).__init__(
            *args, **kwargs)
        self._fields = fields

    @classmethod
    def string_to_point(cls, str):
        a = str.split(',')
        return Point(float(a[1].strip()), float(a[0].strip()))

    def get_or_create_from_string(self, latlng):
        point = self.string_to_point(latlng)

        created = False
        pl = Place.objects.filter(latlng=point).first()

        if pl is None:
            pl = Place.objects.create(latlng=point)
            created = True

        return pl, created


class Place(models.Model):
    objects = PlaceManager()

    title = models.TextField()
    latlng = PointField()

    start_date = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='place_start_date')

    is_ended = models.BooleanField(
        default=True,
        help_text="Is the site or archive still at this location?")
    end_date = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='place_end_date')

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def latitude(self):
        return self.latlng.coords[1]

    def longitude(self):
        return self.latlng.coords[0]

    def match_string(self, latlng):
        s = '{},{}'.format(self.latitude(), self.longitude())
        return s == latlng

    def get_absolute_url(self):
        return reverse(
            'place-detail-view', kwargs={'pk': self.id})


class LearningSite(models.Model):
    title = models.TextField(unique=True)

    place = models.ManyToManyField(Place, blank=True)

    description = models.TextField(null=True, blank=True)
    category = models.ManyToManyField(LearningSiteCategory, blank=True)
    instructional_level = models.ManyToManyField(
        InstructionalLevel, blank=True)
    target_audience = models.ManyToManyField(Audience, blank=True)
    digital_object = models.ManyToManyField(DigitalObject, blank=True)

    established = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='site_established')

    is_defunct = models.BooleanField(
        default=True,
        help_text="Does this learning site still exist?")
    defunct = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='site_defunct')

    notes = models.TextField(null=True, blank=True)
    tags = TaggableManager(blank=True)

    founder = models.TextField(null=True, blank=True)
    corporate_body = models.TextField(null=True, blank=True)

    footnotes = models.ManyToManyField(Footnote, blank=True)

    verified = models.BooleanField(default=False)
    verified_modified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name='site_created_by')
    modified_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name='site_modified_by')

    class Meta:
        ordering = ['title']
        verbose_name = "Site of Teaching & Learning"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('site-detail-view', kwargs={'pk': self.id})

    def empty(self):
        return self.category.count() < 1

    def sort_date(self):
        if self.established:
            (lower, upper) = self.established.wrap()
            if lower and not lower.is_empty():
                return lower.start_date()

        return date.min

    def associates(self):
        lst = LearningSiteRelationship.objects.filter(
            site_one=self).values_list('site_two__id', flat=True)
        lst2 = LearningSiteRelationship.objects.filter(
            site_two=self).values_list('site_one__id', flat=True)
        ids = lst.union(lst2)
        return LearningSite.objects.filter(id__in=ids)

    def has_connections(self):
        return self.associates().exists()

    def connections(self):
        return [site.id for site in self.associates()]

    def group(self):
        category = self.category.first()
        return category.group if category else 'other'

    def get_year_range(self):
        est = self.established.get_year() if self.established else None

        if not self.is_defunct:
            defunct = date.today().year
        else:
            defunct = self.defunct.get_year() if self.defunct else None

        if est and defunct:
            return (est, defunct)
        elif est:
            return (est, est)
        elif defunct:
            return (defunct, defunct)
        else:
            return (None, None)

    def places_by_start_date(self):
        # Sort places by start_date desc, but sort empty dates to the end
        return self.place.all().annotate(
            empty_start_date=Count('start_date')).order_by(
                '-empty_start_date', '-start_date__lower', 'title')

    def established_defunct_display(self):
        return format_date_range(
            self.established, self.is_defunct, self.defunct)

    def tags_display(self):
        return [tag.name for tag in self.tags.all()]


class LearningSiteRelationship(models.Model):
    site_one = models.ForeignKey(
        LearningSite, related_name='site_one', on_delete=models.CASCADE)
    site_two = models.ForeignKey(
        LearningSite, related_name='site_two', on_delete=models.CASCADE)


class ArchivalRepository(models.Model):
    title = models.TextField(unique=True, verbose_name="Repository Title")

    place = models.ForeignKey(
        Place, blank=True, null=True, on_delete=models.SET_NULL)

    description = models.TextField(null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name='repository_created_by')
    modified_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name='repository_modified_by')

    class Meta:
        ordering = ['title']
        verbose_name = "Archival Repository"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'archival-repository-detail-view', kwargs={'pk': self.id})


class ArchivalCollection(models.Model):
    collection_title = models.TextField(verbose_name="Collection Title")
    repository = models.ForeignKey(ArchivalRepository,
                                   on_delete=models.CASCADE)

    description = models.TextField(null=True, blank=True)
    learning_sites = models.ManyToManyField(LearningSite, blank=True)
    finding_aid_url = models.URLField(null=True, blank=True)
    linear_feet = models.FloatField(null=True, blank=True)
    record_format = models.ManyToManyField(ArchivalRecordFormat, blank=True)

    inclusive_start = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='collection_start')
    inclusive_end = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='collection_end')

    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name='collection_created_by')
    modified_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name='collection_modified_by')

    class Meta:
        ordering = ['collection_title']
        verbose_name = "Archival Collection"

    def __str__(self):
        return self.collection_title


class ArchivalCollectionSuggestion(models.Model):
    person = models.TextField(verbose_name="Your Name")
    person_title = models.TextField(verbose_name="Your Title")
    email = models.EmailField(verbose_name="Your Email Address")

    repository_title = models.TextField()
    collection_title = models.TextField()

    latlng = PointField()
    title = models.TextField(verbose_name="Address")

    description = models.TextField(null=True, blank=True)
    finding_aid_url = models.URLField(null=True, blank=True)
    linear_feet = models.FloatField(null=True, blank=True)
    record_format = models.ManyToManyField(ArchivalRecordFormat, blank=True)

    inclusive_start = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='suggestion_start')
    inclusive_end = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='suggestion_end')

    archival_collection = models.ForeignKey(
        ArchivalCollection, null=True, blank=True,
        on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['repository_title', 'collection_title']

    def get_or_create_repository(self):
        try:
            repo = ArchivalRepository.objects.get(
                title=self.repository_title)
        except ArchivalRepository.DoesNotExist:
            (place, created) = Place.objects.get_or_create(
                title=self.title,
                latlng=self.latlng,
                start_date=None, end_date=None)
            repo = ArchivalRepository.objects.create(
                place=place, title=self.repository_title)
        return repo

    def get_or_create_collection(self, repo):
        try:
            collection = ArchivalCollection.objects.get(
                collection_title=self.collection_title, repository=repo)
        except ArchivalCollection.DoesNotExist:
            collection = ArchivalCollection.objects.create(
                repository=repo, collection_title=self.collection_title,
                description=self.description,
                finding_aid_url=self.finding_aid_url,
                linear_feet=self.linear_feet,
                inclusive_start=self.inclusive_start,
                inclusive_end=self.inclusive_end)

        return collection

    def add_notes(self, collection):
        notes = 'Suggested by {}, {}'.format(self.person, self.person_title)
        if collection.notes:
            collection.notes = collection.notes + ' ' + notes
        else:
            collection.notes = notes
        collection.save()

    def convert_to_archival_collection(self):
        if self.archival_collection is not None:
            return self.archival_collection

        repo = self.get_or_create_repository()
        collection = self.get_or_create_collection(repo)
        self.add_notes(collection)

        self.archival_collection = collection
        self.save()

        return collection
