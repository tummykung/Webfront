from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext as _
# Create your models here.

from ASHMC.main.models import Dorm

import datetime


class Ballot(models.Model):
    """For example, a ballot for ASHMC President would have
        candidates (actually PersonCandidates).

        Multiple ballots can appear in a measure; that is,
        you can have a ballot for ASHMC President election and
        one for VP election in the same measure.
    """

    TYPES = (
        ("PL", "Popularity"),
    )

    measure = models.ForeignKey('Measure', null=True)

    display_position = models.IntegerField(default=1)

    title = models.CharField(max_length=50)
    blurb = models.TextField()

    can_write_in = models.BooleanField(default=False)
    is_secret = models.BooleanField(default=True)

    def __unicode__(self):
        return u"Ballot #{}: {}".format(self.id, self.title)

    class Meta:
        unique_together = (('measure', 'display_position'), ('measure', 'title'))


class Measure(models.Model):
    """A collection of ballots. This is probably where you'd want
    to calculate things like quorum."""

    name = models.CharField(max_length=50)
    summary = models.TextField(blank=True, null=True)

    vote_start = models.DateTimeField(default=datetime.datetime.now)
    vote_end = models.DateTimeField()

    is_open = models.BooleanField(default=True)

    real_type = models.ForeignKey(ContentType, editable=False, null=True)

    def _get_real_type(self):
        return ContentType.objects.get_for_model(type(self))

    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    class Meta:
        verbose_name = _('Mesure')
        verbose_name_plural = _('Mesures')

    def __unicode__(self):
        return u"{}: Ballots {}".format(self.name, self.ballot_set.all())

    def save(self, *args, **kwargs):
        if not self.id:
            self.real_type = self._get_real_type()
        super(Measure, self).save(*args, **kwargs)


class DormMeasure(Measure):
    dorm = models.ForeignKey(Dorm)
    number = models.IntegerField()

    class Meta:
        unique_together = ('dorm', 'number',)


class Vote(models.Model):

    account = models.ForeignKey(User, null=True)
    measure = models.ForeignKey(Measure)

    class Meta:
        verbose_name = _('Vote')
        verbose_name_plural = _('Votes')
        # Never vote twice.
        unique_together = (('account', 'measure'),)

    def __unicode__(self):
        return u"{} in #{}-{}".format(self.account, self.measure.id, self.measure.name)


class PopularityVote(models.Model):
    """Represents the most common kind of vote: where each student
    gets a single vote."""

    vote = models.ForeignKey(Vote)
    ballot = models.ForeignKey(Ballot)
    candidate = models.ForeignKey("Candidate", null=True, blank=True)
    write_in_value = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('PopularityVote')
        verbose_name_plural = _('PopularityVotes')

    def __unicode__(self):
        if self.candidate is not None:
            votee = self.candidate
        else:
            votee = self.write_in_value

        return "{} ({}) for {}".format(self.vote, self.ballot, votee)


class Candidate(models.Model):
    """An abstract candidate, be it a person or a law or funding"""

    ballot = models.ForeignKey(Ballot)

    description = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True, null=True)

 # This FK is what makes the polymorphic magic work (esp. for printing)
    real_type = models.ForeignKey(ContentType, editable=False, null=True)

    class Meta:
        unique_together = (('ballot', 'title'),)

    def _get_real_type(self):
        return ContentType.objects.get_for_model(type(self))

    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    def save(self, *args, **kwargs):
        if not self.id:
            self.real_type = self._get_real_type()
        super(Candidate, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"{}".format(self.title)


class PersonCandidate(Candidate):
    user = models.ForeignKey(User, null=True)

    def save(self, *args, **kwargs):
        self.title = self.user.get_full_name()
        super(PersonCandidate, self).save(*args, **kwargs)

