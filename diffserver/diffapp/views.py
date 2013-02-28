# coding: utf-8

import keyword
import re
from collections import defaultdict
from StringIO import StringIO

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import RequestContext

from diffapp.models import CommitSequence, Diff, LineComment


def index(request):
    LAST_N = 20
    sequences = CommitSequence.objects.order_by('-id').prefetch_related('commits')[:LAST_N]
    c = {
        'sequences': sequences,
    }
    return render(request, "index.html", c)


def show_commit_sequence(request, object_id):
    """ TODO отрефакторить, вынести в шаблоны и пр.
    """
    outfile = StringIO()
    try:
        commit_sequence = CommitSequence.objects.filter(pk=object_id)\
                .prefetch_related('commits', 'commits__diffs', 'commits__diffs__comments')\
                [:1][0]
    except IndexError:
        return HttpResponse(code=404)

    def diff_to_html(self, commit_number, number_in_commit):
        print >>outfile, '<h4 class="diff"><span>', self.filename, '</span>'
        anchor = 'commit%s-file%s' % (commit_number, number_in_commit)
        print >>outfile, u'<a class="anchor-thingy jumps-to-anchor diff-anchor" id="{anchor}" href="#{anchor}">¶</a>'.format(**locals()) , '</h4>'
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
                      u'''<td class="line" style="{this_row_top_border}">&nbsp;'''.format(**locals())
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
        print >>outfile, '<h3 class="commit"><span>', self.oneline_summary, '</span>'
        anchor = self.make_anchor()
        print >>outfile, u'<a class="anchor-thingy jumps-to-anchor commit-anchor" id="{anchor}" href="#{anchor}">¶</a>'.format(**locals()), '</h3>'
        print >>outfile, '<pre>' + '\n'.join(self.head).replace('<', '&lt;') + '</pre>'

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


def export_comments(request, commit_sequence_id):
    """ Экспорт комментов для помещения в trac """
    sequence = get_object_or_404(CommitSequence, pk=commit_sequence_id)
    comments = LineComment.objects.filter(diff__commit__commit_sequence__pk=commit_sequence_id)\
            .select_related('diff').order_by('diff__filename', 'pk')

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
        line_index_0 = int(comment.first_line_anchor.split('-')[-1][4:], 16)
        line_index_1 = int(comment.last_line_anchor.split('-')[-1][4:], 16)

        if (line_index_0, line_index_1) in already_commented_line_spans:
            continue
        already_commented_line_spans.add((line_index_0, line_index_1))

        lines = comment.diff.lines[line_index_0 : line_index_1 + 1]

        # в районе какой строки в файле искать этот кусок?
        old_line_numbers = filter(None, [line.old_li for line in lines])
        new_line_numbers = filter(None, [line.new_li for line in lines])
        around_line_no = (new_line_numbers or old_line_numbers or [0])[0]

        text_lines = [line.line for line in lines]
        rendered_lines = [
            u'%5d%s %s' % (
                line.new_li or '',
                ONE_CHAR_LINE_TYPES.get(line.type, ' '),
                line.line
            ) for line in lines
        ]

        print >>exported, ' *', comment.diff.filename, '@', around_line_no
        print >>exported, ''
        print >>exported, '{{{'
        for line in rendered_lines:
            print >>exported, line
        print >>exported, '}}}'
        for line in comment.text.split('\n'):
            print >>exported, '    ', line
        print >>exported, ''

    return HttpResponse(exported.getvalue(), mimetype='text/plain')
