# coding: utf-8
"""

Submit a sequence of git commits to diffcommenter (code review tool).

        to-review

            submits commits from current git branch, starting from first
            commit not present in `master` branch

        to-review 1ef3c44

            submits commit sequence from 1ef3c44 (not included) to HEAD

        to-review --branch origin/feature/mega_feature

            submits commits from specific branch

        to-review --diff

            submits all commits as a single diff

        to-review --only 1ef3c44

            submits only a single specified commit

        to-review -f file1.txt -f file2.txt

            submits several entire files, not diffs
            (does not require the files to be inside a Git repository)
"""
from __future__ import print_function
from optparse import OptionParser
from subprocess import Popen, PIPE
import os
import sys

# If python3
if sys.version_info[0] < 3:
    from urllib2 import urlopen, HTTPError
    from urllib import urlencode
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser
    from urllib.error import HTTPError
    from urllib.request import urlopen
    from urllib.parse import urlencode

CLIENT_VERSION = None


CONFIG_FILE_NAME = '.diffcommenter'
API_URL = '%s/submit-diff-api/'


def die(post_death_note):
    print(post_death_note, file=sys.stderr)
    exit(1)


def find_config():
    env_path = os.environ.get('DIFFCONFIG')
    if env_path:
        if os.path.isfile(env_path):
            config = ConfigParser()
            config.read([env_path])
            return config
        else:
            die('Error: path to config DIFFCONFIG is invalid')

    thisdir = os.path.abspath('.')
    while thisdir != '/':
        config_path = os.path.join(thisdir, CONFIG_FILE_NAME)
        if os.path.isfile(config_path):
            config = ConfigParser()
            config.read([config_path])
            return config

        thisdir = os.path.abspath(os.path.dirname(thisdir))
    die('Error: configuration file ("%s") is not found in this or any of the parent directories.' % CONFIG_FILE_NAME)


config = find_config()


def get_current_branch_name():
    """ Вернет имя текущей ветки (не работает, если текущая - одна из origin/) """
    process = Popen("git show-ref | grep `git rev-parse HEAD`", shell=True, stdout=PIPE)
    out, err = process.communicate()
    if process.returncode != 0:
        die('`git branch` failed')
    out = out.decode().split('\n')[0].strip()
    # out ~ "9f9dd42e860c7696a58bd0810cc241e058cfab4e refs/heads/feature/my_mega_feature_#13538"

    sha1, ref = out.strip().split(' ', 1)
    ref_parts = ref.split('/', 2)
    return ref_parts[2]


DUMMY_COMMIT_HEADER = """commit 0000000000000000000000000000000000000000
Author: Committer Guy <committer.guy@gmail.com>
Date:   Thu Jan 1 00:00:01 2000 +0400

    Fake commit containing "git diff" result

"""


def read_diff(only_commit=None, from_commit=None, base_branch='develop', single_diff=False, head='HEAD', diff_context=15):
    """ Считывает описание набора коммитов в ветке (git show). Возвращает строку.

        :param only_commit: вернуть описание только коммита с этим хешом
        :param from_commit: вернуть описание коммитов, начиная со следующего после from_commit и до HEAD включительно
        :param base_branch: если не указан ни from_commit, ни only_commit - вернуть все коммиты в ветке после ответвления
                            этой ветки от base_branch (по умолч. develop)
        :param single_diff: если True, то схлопнуть все коммиты в один (вместо git show делать git diff)
        :param head: по умолчанию HEAD, можно заменить на имя чужой ветки (на что повлияет - см. описание from_commit)
    """
    assert not (only_commit and from_commit)

    if single_diff:
        cmd = "git diff "
    else:
        cmd = "git show -U%s " % diff_context

    if only_commit:
        process = Popen(cmd + "%s" % only_commit, shell=True, stdout=PIPE)
    elif from_commit:
        process = Popen(cmd + "%s..%s" % (from_commit, head), shell=True, stdout=PIPE)
    else:
        process = Popen(cmd + "`git merge-base %(head)s %(basebranch)s`..%(head)s" % {
                'head': head,
                'basebranch': base_branch,
            }, shell=True, stdout=PIPE)
    out, err = process.communicate()
    if process.returncode != 0:
        die('`%s` failed' % cmd)

    if single_diff:
        out = DUMMY_COMMIT_HEADER + out

    return out


def make_fake_diff_from_files(filenames):
    """ Соорудить что-то похожее на вывод diff, если бы добавили несколько новых файлов """
    difflines = []
    difflines.extend([
        "commit 0000000000000000000000000000000000000000",
        "Author: Committer Guy <commiter.guy@gmail.com>",
        "Date:   Tue Feb 19 13:46:55 2013 +0400",
        "",
        "    Fake commit",
        "",
    ])

    for filename in filenames:
        file_lines = ['+' + line.rstrip('\n') for line in open(filename).readlines()]
        difflines.extend([
            "diff --git a/{} b/{}".format(filename, filename),
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            "+++ a/{}".format(filename),
            "@@ -0,0 +1,{} @@".format(len(file_lines)),
        ])
        difflines.extend(file_lines)
    return '\n'.join(difflines)


def send_diff_to_server(title, diff):
    """ отправка диффа на сервер """
    if sys.version_info[0] < 3:
        diff = diff.encode('utf-8') if isinstance(diff, unicode) else diff

    data = {
        'title': title,
        'diff': diff,
        'login': config.get("Diffcommenter", "login"),
        'password': config.get("Diffcommenter", "password"),
        'client_version': str(CLIENT_VERSION),
    }
    if not data['password']:
        if sys.version_info[0] < 3:
            data['password'] = raw_input("Enter Diffcommenter password for %s:" % data['login'])
        else:
            data['password'] = input("Enter Diffcommenter password for %s:" % data['login'])

    url = API_URL % config.get("Diffcommenter", "url")
    try:
        if sys.version_info[0] < 3:
            print(urlopen(url, urlencode(data)).read())
        else:
            print(urlopen(url, urlencode(data).encode("utf-8")).read().decode('utf-8'))
    except HTTPError as err:
        code = err.getcode()
        print('HTTP Error code: ', code)
        if code == 400:
            print(err.read())


if __name__ == '__main__':
    parser = OptionParser(usage=__doc__)

    parser.add_option("--branch", "-b", dest="branch", default=None, help=u"use this branch instead of HEAD")
    parser.add_option("--base", dest="base", default='origin/master', help=u"use this branch instead of master")
    parser.add_option("--only", "--commit", "-o", "-c", dest="only_commit", default=None, help=u"send only specified commit to review")
    parser.add_option("--diff", "-d", dest="single_diff", default=None, action="store_true", help=u"collapse all commits in range into a single diff")
    parser.add_option("--file", "-f", dest="review_files", default=None, action="append", help=u"review an entire single file instead of a git diff")
    parser.add_option("-C", dest="diff_context", default="15", help=u"number of lines for diff context")
    (options, args) = parser.parse_args()
    from_commit = args[0] if len(args) > 0 else None

    if options.review_files:
        branch = ', '.join(options.review_files)
        if len(branch) > 50:
            branch = branch[:47] + "..."
        diff = make_fake_diff_from_files(options.review_files)
    else:
        branch = options.branch or get_current_branch_name()
        head = options.branch or 'HEAD'

        diff = read_diff(
            base_branch=options.base,
            only_commit=options.only_commit,
            from_commit=from_commit,
            single_diff=options.single_diff,
            head=head,
            diff_context=options.diff_context,
        )
    send_diff_to_server(branch, diff)
