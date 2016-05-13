# coding: utf-8

from StringIO import StringIO
from collections import defaultdict
import keyword
import os
import re

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from diffapp.models import CommitSequence, Diff, LineComment
from diffapp.diffimport import make_commit_sequence


def index(request):
    LAST_N = 20
    sequences = CommitSequence.objects.order_by('-id').prefetch_related('commits')[:LAST_N]
    c = {
        'sequences': sequences,
        'settings': settings,
    }
    return render(request, "index.html", c)


def register(request):
    class RegisterForm(forms.Form):
        username = forms.CharField(u'Login')
        password = forms.CharField(u'Password', widget=forms.PasswordInput)
        repeat_password = forms.CharField(u'Password (again)', widget=forms.PasswordInput)

        def clean(self):
            cleaned_data = super(RegisterForm, self).clean()
            username = cleaned_data.get('username')
            if username and User.objects.filter(username=username).exists():
                raise forms.ValidationError('User "%s" is already registered' % username)
            pw = cleaned_data.get('password')
            pw2 = cleaned_data.get('repeat_password')
            if pw and pw2 and pw != pw2:
                raise forms.ValidationError('Passwords do not match')
            return cleaned_data

    form = RegisterForm(request.POST or None)
    if form.is_valid():
        args = dict(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )

        User.objects.create_user(**args)
        auth_user = authenticate(**args)
        login(request, auth_user)
        return HttpResponseRedirect(reverse('home'))

    c = {
        'form': form,
    }
    return render(request, "registration/register.html", c)


def show_commit_sequence(request, object_id):
    """ TODO отрефакторить, вынести в шаблоны и пр.
    """
    outfile = StringIO()
    try:
        commit_sequence = CommitSequence.objects.filter(
            pk=object_id
        ).prefetch_related(
            'commits', 'commits__diffs', 'commits__diffs__comments'
        )[:1][0]
    except IndexError:
        return HttpResponse(status=404)

    def diff_to_html(self, commit_number, number_in_commit):
        heading = self.filename
        print >>outfile, '<h4 class="diff"><span>', heading.replace('<', '&lt;'), '</span>'
        anchor = self.make_anchor(number_in_commit)
        print >>outfile, u'<a class="anchor-thingy jumps-to-anchor diff-anchor" id="{anchor}" href="#{anchor}">¶</a>'.format(**locals()), '</h4>'
        print >>outfile, '<pre>' + '\n'.join(self.head) + '</pre>'
        print >>outfile, '''<table data-diff-pk="{self.pk}" width="100%" cellspacing="0" class="difftable">
        <tr>
            <th width="37">Older#</th>
            <th width="37">Newer#</th>
            <th>Line</th>
        </tr>'''.format(**locals())

        streak = ''
        border_colors_by_type = {
            'old': 'red',
            'new': 'green',
        }

        BORDER_PATTERN = 'border-top: solid 1px %s'

        python_kw_set = set(keyword.kwlist)

        comments_by_last_line_anchor = defaultdict(list)
        for comment in self.comments.all().order_by('id'):
            comments_by_last_line_anchor[comment.last_line_anchor].append(comment)

        for line_i, line in enumerate(self.lines):
            this_row_top_border = ''

            if streak:
                if line.type != streak:
                    this_row_top_border = BORDER_PATTERN % border_colors_by_type[streak]
                    streak = None

            if not streak and line.type in ('new', 'old'):
                streak = line.type
                this_row_top_border = BORDER_PATTERN % border_colors_by_type[streak]
            fmt_line = line.line.replace('&', '&amp;').replace('<', '&lt;').replace(' ', '&nbsp;')
            fmt_line = fmt_line or '&nbsp;'

            for kword in python_kw_set:
                fmt_line = re.sub(r'\b%s\b' % kword, '<b>%s</b>' % kword, fmt_line)

            anchor = 'commit%s-file%s-line%s' % (commit_number, number_in_commit, hex(line_i))
            anchor_insides = 'class="anchor-thingy jumps-to-anchor line-anchor" href="#{anchor}"'.format(**locals())

            if line.type == 'skip':
                row = u'''<td class="lno" colspan="2" width="center">...</td>'''\
                      u'''<td class="line" style="{this_row_top_border}; color: blue "><pre>{fmt_line}</pre>'''.format(**locals())
            elif line.type == 'same':
                row = u'''<td class="lno" ><a {anchor_insides}>{line.old_li}</a></td>'''\
                      u'''<td class="lno" ><a {anchor_insides}>{line.new_li}</a></td>'''\
                      u'''<td class="line" style="{this_row_top_border}"><pre>{fmt_line}</pre>'''.format(**locals())
            elif line.type == 'old':
                row = u'''<td class="lno" ><a {anchor_insides}>{line.old_li}</a></td>'''\
                      u'''<td class="lno" >&nbsp;</td>'''\
                      u'''<td class="line" style="background-color: #FFDDDD; {this_row_top_border}"><pre>{fmt_line}</pre>'''.format(**locals())
            elif line.type == 'new':
                row = u'''<td class="lno" >&nbsp;</td>'''\
                      u'''<td class="lno" ><a {anchor_insides}>{line.new_li}</a></td>'''\
                      u'''<td class="line" style="background-color: #DDFFDD; {this_row_top_border}"><pre>{fmt_line}</pre>'''.format(**locals())
            print >>outfile, '<tr id="{anchor}">'.format(**locals())
            print >>outfile, row

            for comment in comments_by_last_line_anchor[anchor]:
                print >>outfile, render_to_string(
                    "comment_ajax.html",
                    RequestContext(request, {
                        'comment': comment,
                    })
                )

            print >>outfile, '</td>'
            print >>outfile, '</tr>'
        print >>outfile, '</table>'
    # end of diff_to_html

    def commit_to_html(self):
        print >>outfile, '<hr>'
        heading = self.oneline_summary
        print >>outfile, '<h3 class="commit"><span>', heading, '</span>'
        anchor = self.make_anchor()
        print >>outfile, u'<a class="anchor-thingy jumps-to-anchor commit-anchor" id="{anchor}" href="#{anchor}">¶</a>'.format(**locals()), '</h3>'
        print >>outfile, '<pre>' + '\n'.join(self.head).replace('<', '&lt;') + '</pre>'

        print >>outfile, u'<ul class="commit-file-list">'
        for i, diff in enumerate(self.diffs.all()):
            anchor = diff.make_anchor(i)
            print >>outfile, u'<li><a class="anchor-thingy jumps-to-anchor toc_link" href="#{anchor}">{diff.filename}</a></li>'.format(**locals())
        print >>outfile, u'</ul>'

        for i, diff in enumerate(self.diffs.all()):
            diff_to_html(diff, self.pk, i)

    def sequence_to_html(self):
        for commit in self.commits.all():
            commit_to_html(commit)
    # end of sequence_to_html

    sequence_to_html(commit_sequence)
    c = {
        'commit_sequence_html': outfile.getvalue(),
        'commit_sequence': commit_sequence,
        'comments': LineComment.objects.filter(
            diff__commit__commit_sequence=commit_sequence)
    }
    return render(request, "commit_sequence.html", c)


def ajax_new_comment(request, commit_sequence_id):
    """ AJAX-вьюха для создания нового коммента.

        :param commit_sequence_id: id пачки коммитов
        :param request.GET['diff_id']: id диффа внутри этой пачки
        :param request.GET['first_line_anchor']: индентификатор первой строки в комментируемом диапазоне
        :param request.GET['last_line_anchor']: индентификатор первой строки в комментируемом диапазоне
    """
    if not all([
            request.GET.get('first_line_anchor'),
            request.GET.get('last_line_anchor')]):
        return HttpResponse(status=400)

    if not request.user.is_authenticated():
        return HttpResponse(u'You must be logged in to comment', status=403)

    diff = get_object_or_404(Diff,
        pk=request.GET.get('diff_id'),
        commit__commit_sequence__pk=commit_sequence_id
    )
    comment = LineComment(
        diff=diff,
        user=request.user,
        text='',
        first_line_anchor=request.GET.get('first_line_anchor'),
        last_line_anchor=request.GET.get('last_line_anchor')
    )
    comment.save()

    c = {
        'comment': comment,
    }
    return render(request, "comment_ajax.html", c)


def ajax_save_comment(request, commit_sequence_id):
    """ AJAX-вьюха для сохранения текста уже существующего коммента.

        :param commit_sequence_id: id пачки коммитов
        :param request.POST['comment_id']: id коммента
        :param request.POST['text']: новый текст коммента
    """
    if not all([
            request.POST.get('comment_id'),
            request.POST.get('text')]):
        return HttpResponse(status=400)

    if not request.user.is_authenticated():
        return HttpResponse(u'You must be logged in to comment', status=403)

    comment = get_object_or_404(LineComment,
        pk=request.POST.get('comment_id'),
        diff__commit__commit_sequence__pk=commit_sequence_id
    )

    if comment.user.pk != request.user.pk:
        return HttpResponse(u'Only author can change his comments', status=403)

    comment.text = request.POST['text']
    comment.save()

    return HttpResponse('OK')


def ajax_del_comment(request, commit_sequence_id):
    """ AJAX-вьюха для удаления коммента.

        :param commit_sequence_id: id пачки коммитов
        :param request.POST['comment_id']: id коммента
    """
    if not request.POST.get('comment_id'):
        return HttpResponse(status=400)

    if not request.user.is_authenticated():
        return HttpResponse(u'You must be logged in to delete comments', status=403)

    comment = get_object_or_404(LineComment,
        pk=request.POST.get('comment_id'),
        diff__commit__commit_sequence__pk=commit_sequence_id
    )

    if comment.user.pk != request.user.pk:
        return HttpResponse(u'Only author can delete his comments', status=403)

    comment.delete()

    return HttpResponse('OK')


def export_comments_redmine(request, commit_sequence_id):
    """ Экспорт комментов для помещения в Redmine """
    sequence = get_object_or_404(CommitSequence, pk=commit_sequence_id)
    comments = LineComment.objects.filter(diff__commit__commit_sequence__pk=commit_sequence_id)\
            .select_related('diff', 'diff__commit').order_by('first_line_anchor', 'added')

    exported = StringIO()
    url = settings.ROOT_URL + sequence.get_edit_url()
    print >>exported, url
    print >>exported, ''

    ONE_CHAR_LINE_TYPES = {
        'old': u'-',
        'new': u'+',
    }

    # для каждого диапазона строк выводим только первый, исходный коммент
    already_commented_line_spans = set()  # of (start_index, end_index)

    for comment in comments:
        # anchor ~ "commit1-file1-line0x15"
        # адовый ад
        comment.line_index_0 = int(comment.first_line_anchor.split('-')[-1][4:], 16)

    comments = sorted(comments, key=lambda c: (c.diff.commit_id, c.diff.pk, c.line_index_0))

    for comment in comments:
        # anchor ~ "commit1-file1-line0x15"
        # адовый ад
        line_index_0 = int(comment.first_line_anchor.split('-')[-1][4:], 16)
        line_index_1 = int(comment.last_line_anchor.split('-')[-1][4:], 16)

        #if (line_index_0, line_index_1) in already_commented_line_spans:
        #    continue
        already_commented_line_spans.add((line_index_0, line_index_1))

        lines = comment.diff.lines[line_index_0: line_index_1 + 1]

        # в районе какой строки в файле искать этот кусок?
        old_line_numbers = filter(None, [line.old_li for line in lines])
        new_line_numbers = filter(None, [line.new_li for line in lines])
        around_line_no = (new_line_numbers or old_line_numbers or [0])[0]

        rendered_lines = [
            u'%5s%s %s' % (
                line.new_li or '',
                ONE_CHAR_LINE_TYPES.get(line.type, ' '),
                line.line
            ) for line in lines
        ]

        commented_chunk_title = u'**%s** @ %s' % (comment.diff.filename, around_line_no)
        print >>exported, '_' + comment.diff.commit.short_hash + '_', commented_chunk_title
        print >>exported, ''
        print >>exported, '<pre>'
        for line in rendered_lines:
            print >>exported, line
        print >>exported, '</pre>'
        for line in comment.text.split('\n'):
            shifted_line = ('    ' + line).rstrip()
            print >>exported, shifted_line
        print >>exported, ''
        print >>exported, ''

    return HttpResponse(exported.getvalue(), mimetype='text/plain')


@csrf_exempt
def submit_diff_api(request):
    """ Вьюха для API публикации диффов """
    title = request.POST.get('title')
    diff = request.POST.get('diff')
    login = request.POST.get('login')
    password = request.POST.get('password')
    client_version = request.POST.get('client_version')
    if client_version != settings.CLIENT_VERSION:
        return HttpResponseBadRequest(
            'Version of your client ({0}) is outdated. '
            'Current version is {1}. '
            'Redownload to-review.py. \n\n'
            '    wget "{2}"'.format(
                client_version,
                settings.CLIENT_VERSION,
                request.build_absolute_uri(reverse('download_to_review'))
            )
        )
    if not all((title, diff, login, password)):
        return HttpResponse('Not all parameters are specified (title, diff, login, password - something was empty)', status=400)

    user = get_object_or_404(User, username=login)
    if not user.check_password(password):
        return HttpResponse('Password is incorrect', status=403)

    diff_lines = diff.split('\n')

    sequence = make_commit_sequence(diff_lines, user=user, title=title)
    url = request.build_absolute_uri(sequence.get_edit_url())
    return HttpResponse(url)


def download_to_review(request):
    "Download to-review.py and embed current client version in it"
    to_review_path = os.path.join(settings.STATIC_ROOT, 'to-review.py')
    with open(to_review_path, 'r') as f:
        to_review = f.read()
    to_review = to_review.replace(
        'CLIENT_VERSION = None',
        'CLIENT_VERSION = "{0}"'.format(settings.CLIENT_VERSION)
    )
    response = HttpResponse(to_review)
    response['content-type'] = 'application/python'
    return response
