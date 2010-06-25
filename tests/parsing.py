#!/usr/bin/env python

import magictest
from magictest import MagicTest as TestCase

import clevercss
from clevercss.grammar import grammar
from codetalker.pgm.grammar import Text, ParseError
from codetalker.pgm.errors import *

class Tokenize(TestCase):
    def tokens(self):
        text = Text('hello = world')
        tokens = grammar.get_tokens(text).get_all()
        self.assertEqual(len(tokens), 6)
        self.assertEqual(tokens[2].charno, 7)
        self.assertEqual(tokens[-2].value, 'world')

    def token_lines(self):
        text = Text('hello\nworld = 6')
        tokens = grammar.get_tokens(text).get_all()
        self.assertEqual(len(tokens), 8)
        self.assertEqual(tokens[-2].lineno, 2)


class Parse(TestCase):
    def parse(self):
        text = 'hello=orld\n\nother=bar\n'
        tree = check_parse(text)

    def rule_def(self):
        text = 'div:\n  a = b\n  @import(d)'
        tree = check_parse(text)

    def selectors(self):
        text = '#some:\n stuff = 3\n\n#other .stuff:\n k = ok'
        tree = check_parse(text)

    def hyphen(self):
        text = '.a-b-c:\n and = other'
        tree = check_parse(text)

    def color(self):
        check_parse('five = #555\n\na = #666666')
        try:
            check_parse('one = #1111')
            raise Exception('supposed to fail on #1111')
        except:
            pass

    def attr(self):
        check_parse('one:\n two: 4\n three = 7')
        check_parse('one:\n -moz-something: 17')
        check_fail('two: 4')
        check_fail('one:\n -moz -space: 5')

    def neg_number(self):
        check_parse('one = -10')
        check_parse('one = -10px')
        check_parse('one = 10%')
        check_parse('one = -10em')
        check_parse('one = -10%')

    def url(self):
        check_parse('one = url("hello.png")')

def make_pass(grammar, text):
    def meta(self):
        try:
            return grammar.process(text)
        except ParseError:
            return grammar.process(text, debug=True)
    return meta

def make_fail(grammar, text):
    def meta(self):
        try:
            tree = grammar.process(text)
            self.fail('Expected "%s" to fail' % text.encode('string_escape'))
        except ParseError:
            pass
    return meta

strings = [(
    '',
    # assignment + expressions
    'a = b',
    '\na = b + c',
    'a = b+c/3.0 - 12',
    'a = 12px',
    'a= 12px + 1/4%',
    'a = a b',
    # @declares
    '@import("abc.css")',
    '@dothis()',
    '@other(1, 3, 4+5, 45/manhatten)',
),()]

for i, good in enumerate(strings[0]):
    setattr(Parse, '%d_good' % i, make_pass(grammar, good))
for i, bad in enumerate(strings[1]):
    setattr(Parse, '%d_bad' % i, make_fail(grammar, good))

class Convert(TestCase):
    pass

cases = [('body:\n top: 5', 'body {\n    top: 5;\n}\n', 'basic'),
        ('body:\n top: 2+4', 'body {\n    top: 6;\n}\n', 'add'),
        ('body:\n top: (5+4 - 1) /2', 'body {\n    top: 4;\n}\n', 'math'),
        ('one = 2\nbody:\n top: one', 'body {\n    top: 2;\n}\n', 'vbl'),
        ('one = 2\nbody:\n top: one+3', 'body {\n    top: 5;\n}\n', 'vbl math'),
        ('one = 2\nbody:\n one = 3\n top: one\ndiv:\n top: one',
         'body {\n    top: 3;\n}\n\ndiv {\n    top: 2;\n}\n', 'scoping')]

cases.append(('''.one, .two:
    top: 5px
    .three, .four:
        left: 10px
        & > div:
            bottom: auto''','''\
.one, .two {
    top: 5px;
}
.one .three, .one .four, .two .three, .two .four {
    left: 10px;
}
.one .three > div, .one .four > div, .two .three > div, .two .four > div {
    bottom: auto;
}
''', 'deep selectors'))

cases.append(('''
@something:
    color: green
    width: 25%
    size = 4
    a:
        font-size: 2px*size
        line-height: size*5px
body:
    height: 20px
    @something()
a, div:
    @something()
''', '''\
body {
    height: 20px;
    color: green;
    width: 25%;
}
body a {
    font-size: 8px;
    line-height: 20px;
}

a, div {
    color: green;
    width: 25%;
}
a a, div a {
    font-size: 8px;
    line-height: 20px;
}
''', 'bigold mixin'))
cases.append(('''
@abc(a, b, c=25px):
    color: a
    size: b
    font-size: c - 10px
body:
    @abc(green, 5em)
div:
    @abc(#F00, 2pt, 11px)
''', '''\
body {
    color: green;
    size: 5em;
    font-size: 15px;
}

div {
    color: red;
    size: 2pt;
    font-size: 1px;
}
''', 'mixin w/ args'))

def make_convert(ccss, css):
    def meta(self):
        a = clevercss.convert(ccss, indent=4)
        if a != css:
            print a
            print css
        self.assertEqual(a, css)
    return meta

for i, (ccss, css, name) in enumerate(cases):
    setattr(Convert, 'convert_%d_%s' % (i, name), make_convert(ccss, css))

def check_parse(text):
    try:
        return grammar.process(text)
    except:
        return grammar.process(text, debug=True)

def check_fail(text):
    try:
        grammar.process(text)
    except:
        pass
    else:
        grammar.process(text, debug=True)
        raise Exception('was supposed to fail on \'%s\'' % text.encode('string_escape'))
 
all_tests = magictest.suite(__name__)

# vim: et sw=4 sts=4
