from django.contrib.auth.models import User
from django.contrib.gis.db.models.fields import PointField
from django.contrib.gis.geos.point import Point
from django.db import models
from django.db.models.deletion import SET_NULL
from django.urls.base import reverse
from edtf import text_to_edtf
from taggit.managers import TaggableManager
from writlarge.main.utils import ExtendedDateWrapper


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

    class Meta:
        verbose_name = 'Extended Date Format'

    def wrap(self):
        return ExtendedDateWrapper.create(self.edtf_format)

    def __str__(self):
        (lower, upper) = self.wrap()

        if lower and upper:
            return "%s - %s" % (lower.format(), upper.format())
        else:
            return lower.format()

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


class LearningSite(models.Model):
    title = models.TextField(unique=True)
    latlng = PointField()

    description = models.TextField(null=True, blank=True)
    category = models.ManyToManyField(LearningSiteCategory, blank=True)
    instructional_level = models.ManyToManyField(
        InstructionalLevel, blank=True)
    target_audience = models.ManyToManyField(Audience, blank=True)
    digital_object = models.ManyToManyField(DigitalObject, blank=True)

    established = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=SET_NULL,
        related_name='site_established')
    defunct = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=SET_NULL,
        related_name='site_defunct')

    notes = models.TextField(null=True, blank=True)
    tags = TaggableManager(blank=True)

    founder = models.TextField(null=True, blank=True)

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


class ArchivalRepository(models.Model):
    title = models.TextField(unique=True, verbose_name="Repository Title")
    latlng = PointField()
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
    title = models.TextField(verbose_name="Collection Title")
    repository = models.ForeignKey(ArchivalRepository,
                                   on_delete=models.CASCADE)

    description = models.TextField(null=True, blank=True)
    learning_sites = models.ManyToManyField(LearningSite, blank=True)
    finding_aid_url = models.URLField(null=True, blank=True)
    linear_feet = models.FloatField(null=True, blank=True)
    record_format = models.ManyToManyField(ArchivalRecordFormat, blank=True)

    inclusive_start = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=SET_NULL,
        related_name='collection_start')
    inclusive_end = models.OneToOneField(
        ExtendedDate, null=True, blank=True, on_delete=SET_NULL,
        related_name='collection_end')

    inclusive_start_date = models.DateField(null=True)
    inclusive_end_date = models.DateField(null=True)

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
        ordering = ['title']
        verbose_name = "Archival Collection"

    def __str__(self):
        return self.title


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

    digital_object = models.ManyToManyField(
        DigitalObject, blank=True)

    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

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

    def empty(self):
        return True
