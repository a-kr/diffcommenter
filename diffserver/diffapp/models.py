# coding: utf-8
from django.db import models

# Create your models here.
class CommitSequence(models.Model):
    """ пачка коммитов, отдаваемая в ревью """

    class Meta:
        ordering = ['id']


class Commit(models.Model):
    """ один коммит """
    commit_sequence = models.ForeignKey(CommitSequence, verbose_name=u'Пачка коммитов', related_name='commits', null=True, blank=True)
    sha1 = models.TextField(u'Хэш коммита')
    head_lines = models.TextField(u'Строки метаданных коммита')  # объединенные через \n

    class Meta:
        ordering = ['id']


class Diff(models.Model):
    """ дифф одного файла в коммите """
    commit = models.ForeignKey(Commit, verbose_name=u'Коммит', related_name='diffs', null=True, blank=True)
    filename = models.TextField(u'Путь к файлу')
    head_lines = models.TextField(u'Строки метаданных диффа')  # объединенные через \n
    body_lines = models.TextField(u'Строки диффа в формате unified')  # объединенные через \n

    class Meta:
        ordering = ['id']


class LineComment(models.Model):
    """ коммент к строке в диффе """
    diff = models.ForeignKey(Diff, verbose_name=u'Дифф', related_name='comments')
    line_no = models.IntegerField(u'Индекс строки')

    class Meta:
        ordering = ['id']
