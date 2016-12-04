#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

"""
A simple Multiple HTML to EPUB förmatter

2016
Xaratustrah
"""

import subprocess, sys, re
from jinja2 import Template
from bs4 import BeautifulSoup, Comment
from ebooklib import epub

CMD = 'iconv -f CP1256 -t UTF-8 '
ALIGN = 'right'
LANG = 'fa'
HTML_TMPL = """<!DOCTYPE html>
<html dir="rtl" lang="{{lang}}">
<head>
<meta charset="utf-8">
<meta name="author" content="{{author}}">
<title>{{title}}</title>
</head>
<body dir="rtl">
<h1 style="page-break-before:always;text-align: {{align}};">{{title}}</h1>
<h3 style="text-align: {{align}};">{{author}}</h3>
{{body}}
</body>
</html>
"""


def run_cmd(cmd_string):
    try:
        p = subprocess.Popen(cmd_string.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ok = p.wait()
        out, err = p.communicate()
    except FileNotFoundError:
        out = b''
        err = b''
        ok = True

    return ok, out, err


def read_htmls():
    buffer = ""

    for i in range(9, 228):  # range(9, 228):
        filename = '{}.html'.format(i)
        print('Processing {}'.format(filename))

        ok, out, err = run_cmd(CMD + filename)
        out = out.decode('utf-8')
        soup = BeautifulSoup(out.lower(), 'html.parser')

        # remove unwanted tags
        for tag in soup.findAll(['script', 'head', 'p', 'table', 'div', '!--']):
            if tag.name == 'head' or tag.name == 'script':
                tag.extract()
            if tag.has_attr('class'):
                if 'footer' in tag['class']:
                    tag.extract()

        # remove comments
        comments = soup.findAll(text=lambda text: isinstance(text, Comment))
        [comment.extract() for comment in comments]

        # unwrap unwanted tags
        idx = 0
        for tag in soup.findAll(['div', 'table', 'body', 'html', 'tr', 'td']):
            tag.unwrap()

        # find the index of footnote before removing it
        if '<p class="subscript">' in str(soup):
            idx = str(soup).index('<p class="subscript">')

        # special care for paragraphs
        for tag in soup.findAll(['p']):
            if tag.has_attr('class'):
                if 'subscript' in tag['class']:
                    tag.extract()
                if 'title' in tag['class']:
                    tag['style'] = 'page-break-before:always;font-weight: bold;font-size: 400%;text-align: {};'.format(
                        ALIGN)
                if 'subtitle' in tag['class']:
                    tag['style'] = 'font-weight: bold;text-decoration: underline;text-align: {};'.format(ALIGN)

        out = str(soup)  # make a UTF string out of soup object

        if idx > 0:
            out = out[:idx] + '<br><table border="" cellspacing="0" align="{}"><tr><td>'.format('center') + out[idx:]
            out = out + '</td></tr></table><br>'

        # apply text specific corrections
        for i in range(1, 10):  # replace numbers
            out = out.replace('{}'.format(i), '{}'.format(chr(0x0660 + i)))
        out = out.replace('  ', ' ')  # remove pesky spaces
        out = out.replace('   ', ' ')
        out = out.replace(' ،', '،')
        out = out.replace(' .', '.')
        out = out.replace(' ؟', '؟')
        out = out.replace(' :', ':')
        #out = out.replace('\n', '')
        out = re.sub('\.\s*\\r', '.<br>\n', out)  # fix line breaks
        #out = out.replace('\r', '')

        buffer += out
    return buffer


def write_epub(out_filename, buffer, title, author):
    book = epub.EpubBook()

    # set metadata
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language(LANG)

    book.add_author(author)

    # create chapter
    c1 = epub.EpubHtml(title=title, file_name='content.xhtml', lang=LANG)
    c1.content = buffer

    # add chapter
    book.add_item(c1)

    # define Table Of Contents
    # book.toc = (epub.Link('chap_01.xhtml', 'Introduction', 'intro'),
    #             (epub.Section('Simple book'),
    #              (c1,))
    #             )

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

    # add CSS file
    book.add_item(nav_css)

    # basic spine
    book.spine = ['nav', c1]

    # write to the file
    print('Saving to {}'.format(out_filename))
    epub.write_epub(out_filename, book, {})


def write_html(out_filename, buffer, title, author):
    tmpl = Template(HTML_TMPL)
    html = tmpl.render(title=title, author=author, body=buffer, align=ALIGN, lang=LANG)

    print('Saving to {}'.format(out_filename))
    with open('{}'.format(out_filename), 'w') as f:
        f.write(html)


def main():
    out_filename = sys.argv[1]
    title = sys.argv[2]
    author = sys.argv[3]


    buffer = read_htmls()
    if 'htm' in out_filename.lower():
        write_html(out_filename, buffer, title, author)
    if 'epub' in out_filename.lower():
        write_epub(out_filename, buffer, title, author)


# -------------

if __name__ == '__main__':
    main()
