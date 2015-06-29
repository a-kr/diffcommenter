# coding: utf-8
from django.test import TestCase
from diffapp.diffimport import make_commit_sequence, make_diff
from diffapp.models import CommitSequence, Commit, Diff

EXAMPLE_GIT_SHOW_OUTPUT = u"""commit c28e535f1024e3b22ec05574aa2287aa5338e3dc
Author: Vasya Pupkin <pupkin.vasily@gmail.com>
Date:   Wed Feb 20 21:35:38 2013 +0400

    Оказывается это было в stdlib

diff --git a/a.py b/a.py
index a788f61..2b10ee5 100644
--- a/a.py
+++ b/a.py
@@ -1,3 +1,3 @@
-import b
-if b.quaka(x - y):
+import itertools
+if itertools.iterquaka(x - y):
     return z
diff --git a/b.py b/b.py
deleted file mode 100644
index 6152a79..0000000
--- a/b.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def quaka(x):
-    return x*x

commit 242ce960af361fd307ca2fe61bc0a71c29c28394
Author: Vasya Pupkin <pupkin.vasily@gmail.com>
Date:   Wed Feb 20 21:34:57 2013 +0400

    Рефакторинг

diff --git a/a.py b/a.py
index d62e9f6..a788f61 100644
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
-if x = y:
+import b
+if b.quaka(x - y):
     return z
diff --git a/b.py b/b.py
new file mode 100644
index 0000000..6152a79
--- /dev/null
+++ b/b.py
@@ -0,0 +1,2 @@
+def quaka(x):
+    return x*x

commit f60d7b4858faa696c0581f47ccc81736f9df3ded
Author: Vasya Pupkin <pupkin.vasily@gmail.com>
Date:   Wed Feb 20 21:34:04 2013 +0400

    Добавили a.py

diff --git a/a.py b/a.py
new file mode 100644
index 0000000..d62e9f6
--- /dev/null
+++ b/a.py
@@ -0,0 +1,2 @@
+if x = y:
+    return z
"""

class DiffImportTest(TestCase):
    """ тесты на импорт коммитов из файла """

    def test_import_commit_sequence(self):
        CommitSequence.objects.all().delete()
        make_commit_sequence(EXAMPLE_GIT_SHOW_OUTPUT)

        self.assertEqual(CommitSequence.objects.count(), 1)
        self.assertEqual(Commit.objects.count(), 3)

        commits = Commit.objects.all()[:]

        self.assertEquals(commits[0].sha1, 'f60d7b4858faa696c0581f47ccc81736f9df3ded')
        diffs = commits[0].diffs.all()[:]
        self.assertEquals(len(diffs), 1)
        self.assertEquals(diffs[0].filename, 'a.py')

        self.assertEquals(commits[1].sha1, '242ce960af361fd307ca2fe61bc0a71c29c28394')
        diffs = commits[1].diffs.all()[:]
        self.assertEquals(len(diffs), 2)
        self.assertEquals(diffs[0].filename, 'a.py')
        self.assertEquals(diffs[1].filename, 'b.py')

        self.assertEquals(commits[2].sha1, 'c28e535f1024e3b22ec05574aa2287aa5338e3dc')
        diffs = commits[2].diffs.all()[:]
        self.assertEquals(len(diffs), 2)
        self.assertEquals(diffs[0].filename, 'a.py')
        self.assertEquals(diffs[1].filename, 'b.py')


class DiffParserTest(TestCase):
    """ тест на превращение текста диффа в набор Diff.Line """
    def test_it(self):
        diff_lines = [
            'diff --git a/a.py b/a.py',
            'index d62e9f6..a788f61 100644',
            '--- a/a.py',
            '+++ b/a.py',
            '@@ -1,2 +1,3 @@',
            '-if x = y:',
            '+import b',
            '+if b.quaka(x - y):',
            '     return z',
            ' #blank 1',
            ' #blank 2',
            '@@ -10,12 +11,13 @@',
            ' #blank 9',
            ' def thing(x):',
            '-print a',
            '-print b',
            '+    print a',
            '+    print b',
        ]

        diff = make_diff(diff_lines)
        lines = diff.lines

        expected_line_types_and_numbers = [
            ('old', 1, None),
            ('new', None, 1),
            ('new', None, 2),
            ('same', 2, 3),
            ('same', 3, 4),
            ('same', 4, 5),
            ('skip', None, None),
            ('same', 10, 11),
            ('same', 11, 12),
            ('old', 12, None),
            ('old', 13, None),
            ('new', None, 13),
            ('new', None, 14),
        ]

        actual_line_types_and_numbers = [
            (l.type, l.old_li, l.new_li) for l in lines
        ]

        self.assertEquals(expected_line_types_and_numbers, actual_line_types_and_numbers)
