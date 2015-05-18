# coding: utf-8
import re

from django.conf import settings
from django.db import models


class CommitSequence(models.Model):
    """ пачка коммитов, отдаваемая в ревью """

    title = models.TextField(u'Заголовок', default=u'Безымянная пачка коммитов')
    added = models.DateTimeField(u'Дата добавления', auto_now_add=True)
    user = models.ForeignKey('auth.User', null=True, blank=True, verbose_name=u'Автор', related_name='commit_sequences')

    @models.permalink
    def get_edit_url(self):
        return ("commit_sequence", [self.pk])

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['id']


class Commit(models.Model):
    """ один коммит """
    commit_sequence = models.ForeignKey(CommitSequence, verbose_name=u'Пачка коммитов',
        related_name='commits', null=True, blank=True, on_delete=models.CASCADE)
    sha1 = models.TextField(u'Хэш коммита')
    head_lines = models.TextField(u'Строки метаданных коммита')  # объединенные через \n

    @property
    def head(self):
        return self.head_lines.split('\n')

    @property
    def is_fake(self):
        return set(self.sha1) == set(['0'])

    def make_anchor(self):
        return "commit%s" % self.pk

    @property
    def short_hash(self):
        return self.sha1[:7]

    @property
    def first_line(self):
        comment_lines = [l.strip() for l in self.head if l.startswith('    ')]
        if comment_lines:
            first_line = comment_lines[0]
        else:
            first_line = '(no comment)'
        return first_line

    @property
    def oneline_summary(self):
        return u'%s %s' % (self.short_hash, self.first_line)

    class Meta:
        ordering = ['id']


class Diff(models.Model):
    """ дифф одного файла в коммите """
    commit = models.ForeignKey(Commit, verbose_name=u'Коммит', related_name='diffs',
        null=True, blank=True, on_delete=models.CASCADE)
    filename = models.TextField(u'Путь к файлу')
    head_lines = models.TextField(u'Строки метаданных диффа')  # объединенные через \n
    body_lines = models.TextField(u'Строки диффа в формате unified')  # объединенные через \n

    @property
    def head(self):
        return self.head_lines.split('\n')

    def make_anchor(self, number_in_commit):
        anchor = 'commit%s-file%s' % (self.commit_id, number_in_commit)
        return anchor

    class Line(object):
        """ одна строчка диффа """
        __slots__ = ['old_li', 'new_li', 'type', 'line']

        def __init__(self, old_li, new_li, type, line):
            self.old_li = old_li
            self.new_li = new_li
            self.type = type
            self.line = line

    @property
    def lines(self):
        """ получение списка объектов Diff.Line из содержимого body_lines """
        if hasattr(self, '_cached_lines'):
            return self._cached_lines

        # наша основная задача здесь --- проставить всем строчкам номера
        # по старой и по новой версии файла.

        r1_li = 0  # номер строки в старой версии файла
        r2_li = 0  # номер в новой версии
        diff_t = []
        i = 0

        head = []
        diff = self.body_lines.split('\n')


        while i < len(diff):
            diff[i] = diff[i].replace('\t', '    ').rstrip() or ' '
            type = diff[i][0]
            if type == '@':
                m = re.match(r'^@@ -(\d+),\d+ \+(\d+),\d+ @@(.*)$', diff[i])
                if m:
                    r1_li = int(m.groups()[0])
                    r2_li = int(m.groups()[1])

                    if not (r1_li == 1 or r2_li == 1):
                        diff_t.append((None, None, 'skip', diff[i]))
            elif type == ' ':
                diff_t.append((r1_li, r2_li, 'same', diff[i][1:]))
                r1_li = r1_li + 1
                r2_li = r2_li + 1
            elif type == '-':
                diff_t.append((r1_li, None, 'old', diff[i][1:]))
                r1_li = r1_li + 1
            elif type == '+':
                diff_t.append((None, r2_li, 'new', diff[i][1:]))
                r2_li = r2_li + 1
            i = i + 1

        diff_t = [Diff.Line(*t) for t in diff_t]

        self._cached_lines = diff_t
        return diff_t

    class Meta:
        ordering = ['id']


class LineComment(models.Model):
    """ коммент к строке в диффе """
    diff = models.ForeignKey(Diff, verbose_name=u'Дифф', related_name='comments', on_delete=models.CASCADE)
    added = models.DateTimeField(u'Дата добавления', auto_now_add=True)
    text = models.TextField(u'Текст коммента', blank=True)
    user = models.ForeignKey('auth.User', verbose_name=u'Кто добавил', related_name='comments')

    first_line_anchor = models.TextField(u'Начало комментируемого диапазона')  # по факту это индекс в comment.lines
    last_line_anchor = models.TextField(u'Конец комментируемого диапазона')  # коммент визуально разместится под этой строкой

    def make_anchor(self):
        return "comment%s" % self.pk

    def first_line_with_ellipsis(self):
        lines = self.text.split('\n')
        if not lines:
            return ''
        first_line = lines[0]
        if len(lines) > 1:
            first_line += ' (...)'
        return first_line

    class Meta:
        ordering = ['id']
