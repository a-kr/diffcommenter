# coding: utf-8
import os
import sys
from subprocess import Popen, PIPE
from ConfigParser import ConfigParser
from optparse import OptionParser
import urllib, urllib2


CONFIG_FILE_NAME = '.diffcommenter'
API_URL = '%s/submit-diff-api/'


def die(post_death_note):
    print >>sys.stderr, post_death_note
    exit(1)


def find_config():
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
    out = out.split('\n')[0].strip()
    # out ~ "9f9dd42e860c7696a58bd0810cc241e058cfab4e refs/heads/feature/my_mega_feature_#13538"

    sha1, ref  = out.strip().split(' ', 1)
    ref_parts = ref.split('/', 2)
    return ref_parts[2]


def read_diff(only_commit=None, from_commit=None, base_branch='develop'):
    """ Считывает описание набора коммитов в ветке (git show). Возвращает строку.

        :param only_commit: вернуть описание только коммита с этим хешом
        :param from_commit: вернуть описание коммитов, начиная со следующего после from_commit и до HEAD включительно
        :param base_branch: если не указан ни from_commit, ни only_commit - вернуть все коммиты в ветке после ответвления
                            этой ветки от base_branch (по умолч. develop)
    """
    assert not (only_commit and from_commit)

    if only_commit:
        process = Popen("git show %s" % only_commit, shell=True, stdout=PIPE)
    elif from_commit:
        process = Popen("git show %s..HEAD" % from_commit, shell=True, stdout=PIPE)
    else:
        process = Popen("git show `git merge-base HEAD %s`..HEAD" % base_branch, shell=True, stdout=PIPE)
    out, err = process.communicate()
    if process.returncode != 0:
        die('`git branch` failed')
    return out


def send_diff_to_server(title, diff):
    """ отправка диффа на сервер """
    diff = diff.encode('utf-8') if isinstance(diff, unicode) else diff
    data = {
        'title': title,
        'diff': diff,
        'login': config.get("Diffcommenter", "login"),
        'password': config.get("Diffcommenter", "password"),
    }
    if not data['password']:
        data['password'] = raw_input("Enter Diffcommenter password for %s:" % data['login'])

    url = API_URL % config.get("Diffcommenter", "url")
    response = urllib2.urlopen(url, urllib.urlencode(data))
    print response.read()

if __name__ == '__main__':
    parser = OptionParser()

    parser.add_option("--only", "--commit", "-o", "-c", dest="only_commit", default=None, help=u"send only specified commit to review")
    (options, args) = parser.parse_args()
    from_commit = args[0] if len(args) > 0 else None

    branch = get_current_branch_name()

    base_branch = 'develop'
    if branch.startswith('hotfix/'):
        base_branch = 'master'
    # TODO считать оверрайд из argparse

    diff = read_diff(base_branch=base_branch, only_commit=options.only_commit, from_commit=from_commit)
    send_diff_to_server(branch, diff)
