# coding: utf-8

import keyword
import re

from django.shortcuts import render, get_object_or_404

from diffapp.models import CommitSequence


def index(request):
    c = {
    }
    return render(request, "index.html", c)


def show_commit_sequence(request, object_id):
    """ TODO отрефакторить, вынести в шаблоны и пр.
    """

    from StringIO import StringIO
    outfile = StringIO()
    commit_sequence = get_object_or_404(CommitSequence, pk=object_id)

    def diff_to_html(self, commit_number, number_in_commit):
        print >>outfile, '<h4 class="diff"><span>', self.filename, '</span>'
        anchor = 'commit%s-file%s' % (commit_number, number_in_commit)
        print >>outfile, u'<a class="anchor-thingy jumps-to-anchor diff-anchor" id="{anchor}" href="#{anchor}">¶</a>'.format(**locals()) , '</h4>'
        print >>outfile, '<pre>' + '\n'.join(self.head) + '</pre>'
        print >>outfile, '''<table width="100%" cellspacing="0" class="difftable">
        <tr>
            <th width="37">Older#</th>
            <th width="37">Newer#</th>
            <th>Line</th>
        </tr>'''

        streak = ''
        border_colors_by_type = {
            'old': 'red',
            'new': 'green',
        }

        BORDER_PATTERN = 'border-top: solid 1px %s'

        python_kw_set = set(keyword.kwlist)

        for line_i, line in enumerate(self.lines):
            this_row_top_border = ''

            if streak:
                if line.type != streak:
                    this_row_top_border = BORDER_PATTERN % border_colors_by_type[streak]
                    streak = None

            if not streak and line.type in ('new', 'old'):
                streak = line.type
                this_row_top_border = BORDER_PATTERN % border_colors_by_type[streak]
            fmt_line = line.line.replace('&', '&amp;').replace('<', '&lt;')

            for kword in python_kw_set:
                fmt_line = re.sub(r'\b%s\b' % kword, '<b>%s</b>' % kword, fmt_line)

            anchor = 'commit%s-file%s-line%s' % (commit_number, number_in_commit, hex(line_i))
            anchor_insides = 'class="anchor-thingy jumps-to-anchor line-anchor" id="{anchor}" href="#{anchor}"'.format(**locals())

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
            print >>outfile, '<tr>'
            print >>outfile, row
            #for comment in line.comments:
            #    print >>outfile, '''<div class="comment">'''\
            #                     '''   <div class="comment-title">{comment.date} {comment.author}</div>'''\
            #                     '''   <div class="comment-body"><pre>{comment.text}</pre></div>'''\
            #                     '''</div>'''.format(**locals())
            print >>outfile, '</td>'
            print >>outfile, '</tr>'
        print >>outfile, '</table>'
    # end of diff_to_html

    def commit_to_html(self, commit_number):
        print >>outfile, '<hr>'
        print >>outfile, '<h3 class="commit"><span>', self.oneline_summary, '</span>'
        anchor = "commit%s" % commit_number
        print >>outfile, u'<a class="anchor-thingy jumps-to-anchor commit-anchor" id="{anchor}" href="#{anchor}">¶</a>'.format(**locals()), '</h3>'
        print >>outfile, '<pre>' + '\n'.join(self.head).replace('<', '&lt;') + '</pre>'

        for i, diff in enumerate(self.diffs.all()):
            diff_to_html(diff, commit_number, i)

    def sequence_to_html(self):
        for i, commit in enumerate(self.commits.all()):
            commit_to_html(commit, i)
    # end of sequence_to_html

    sequence_to_html(commit_sequence)
    c = {
        'commit_sequence_html': outfile.getvalue(),
    }
    return render(request, "commit_sequence.html", c)
