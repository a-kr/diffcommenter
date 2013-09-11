# coding: utf-8
"""
    На основе вывода команды git show заполняет модели
"""

from diffapp.models import Diff, Commit, CommitSequence


def make_commit_sequence(git_show_lines, title=None, user=None):
    """
        :param git_show_lines: строчки вывода git show %commit_hash2%..%commit_hash1%
        :returns: новый, сохраненный в БД объект CommitSequence
    """
    if isinstance(git_show_lines, basestring):
        git_show_lines = git_show_lines.replace('\r\n', '\n').split('\n')

    commit_line_spans = []
    current_commit_lines = []

    sequence = CommitSequence()
    sequence.title = title or 'Untitled commit sequence'
    sequence.user = user
    sequence.save()

    i = 0
    while i < len(git_show_lines):
        if git_show_lines[i].startswith('commit '):
            if current_commit_lines:
                commit_line_spans.append(current_commit_lines)
            current_commit_lines = []
        current_commit_lines.append(git_show_lines[i])
        i += 1

    if current_commit_lines:
        commit_line_spans.append(current_commit_lines)

    # мы получили коммиты в обратном временном порядке.
    commit_line_spans = commit_line_spans[::-1]
    commits = [
        make_commit(commit_line_span, commit_sequence=sequence)
        for commit_line_span in commit_line_spans
    ]
    return sequence


def make_commit(lines, commit_sequence=None):
    """
        :param lines: строчки вывода git show %commit_hash%
        :param commit_sequence: пачка коммитов, к которой принадлежит создаваемый коммит
        :returns: новый, сохраненный в БД объект Commit
    """
    assert lines[0].startswith('commit ')
    sha1 = lines[0].split(' ', 1)[1]

    commit = Commit(commit_sequence=commit_sequence)
    head = []
    i = 0

    while i < len(lines):
        if lines[i].startswith('diff '):
            break
        head.append(lines[i].rstrip())
        i += 1

    commit.head_lines = u'\n'.join(head)
    commit.sha1 = sha1
    commit.save()

    current_diff_lines = []

    while i < len(lines):
        if lines[i].startswith('diff '):
            if current_diff_lines:
                make_diff(current_diff_lines, commit=commit)
            current_diff_lines = []
        current_diff_lines.append(lines[i])
        i += 1

    if current_diff_lines:
        make_diff(current_diff_lines, commit=commit)
    return commit


def make_diff(lines, commit=None):
    """
        :param lines: строчки вывода git diff -u file1 file2 (дифф одного файла)
        :param commit: коммит, к которому принадлежит создаваемый дифф
        :returns: новый, сохраненный в БД объект Diff
    """
    assert len(lines) > 2
    assert lines[0].startswith('diff ')

    diff = Diff(commit=commit)

    head = []

    def strip_phony_filename_prefixes(filename):
        if filename.startswith('a/') or filename.startswith('b/'):
            return filename[len('a/'):]
        return filename

    i = 0
    while i < len(lines):
        head.append(lines[i].rstrip())
        if lines[i].startswith('--- '):
            diff.filename = strip_phony_filename_prefixes(lines[i].split(' ', 1)[1])
        if lines[i].startswith('+++ '):
            filename = strip_phony_filename_prefixes(lines[i].split(' ', 1)[1])
            if filename != '/dev/null':
                diff.filename = filename
            break
        i += 1
    diff.head_lines = u'\n'.join(head)
    diff.body_lines = u'\n'.join(line.rstrip() for line in lines[i + 1:])
    diff.save()
    return diff
