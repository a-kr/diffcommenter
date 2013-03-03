# coding: utf-8
"""
    Считывает вывод git show / git diff из stdin и создает новый CommitSequence в БД

"""
import sys


from django.conf import settings
from django.core.management.base import BaseCommand


from diffapp.diffimport import make_commit_sequence


class Command(BaseCommand):
    help = u"Импорт диффа из stdin"

    def handle(self, *args, **options):
        difftext = sys.stdin.read()
        difftext = difftext.decode('utf-8')
        difflines = difftext.split('\n')

        sequence = make_commit_sequence(difflines, title='(stdin)')
        url = settings.ROOT_URL + sequence.get_edit_url()
        print url
