"""This module contains methods to modify links in markup documents"""
import re
import os
try:
    # Python 2
    from urlparse import urlparse
except ImportError:
    # Python 3
    from urllib.parse import urlparse
import mimetypes


LINK_TEMPLATES = {'rst': {'format': '`{title}<{link}>`',
                          'regex': re.compile(r'`(?P<title>[^`]*?)<(?P<link>[^`\n]*?)>`'),
                         },
                  'md': {'format': '[{title}]({link})',
                         'regex': re.compile(r'\[(?P<title>[^\[\]]*?)\]\((?P<link>[^)(]*?)\)'),
                        },
                  'html': {'format': '<{start}src="{link}"{end}>',
                           'regex': re.compile(r'<(?P<start>[^><]*?)src\s*=\s*"(?P<link>.*?)"(?P<end>[^<]*?)>'),
                          },
                 }


def is_relative(path):
    """whether `path` is relative"""
    return not bool(urlparse(path).netloc)


def get_html_path(path, filetype):
    """
    Returns path with extension html if original extension is md or rst or
    if filetype is markdown and path has no extension at all.
    """
    basepath, ext = os.path.splitext(path)
    if ext in ('.md', '.rst') or (filetype == 'md' and ext == '' and not basepath.endswith('/')):
        return basepath + '.html'
    return path


def is_path_image(path):
    is_image = False
    mimetype = mimetypes.guess_type(path)[0]
    if mimetype is not None:
        is_image = True if mimetype.startswith('image') else False
    return is_image


def fixlink(link, level, linktype, filetype=None):
    if is_relative(link) and not link.startswith('#'):
        splitted = [value for value in get_html_path(link, filetype).split('/')
                    if value]
        if is_path_image(link) and linktype != 'html':
            splitted = [os.pardir] * level + splitted
        else:
            if len(splitted) > level:
                splitted = splitted[level:]
            else:
                splitted = [os.pardir] * level + splitted
        return '/'.join(splitted)
    return link


def fix_relative_links(content, source_path):
    """
    Modifies any relative links according to the `source_path`

    Parameters
    ----------
    content: str
        string where modifications should be performed

    source_path: str
        path of the source file from which content was read
    """
    filetype = os.path.splitext(source_path)[1].lstrip('.')
    level = [value for value in source_path.replace(os.path.sep, '/').split('/')
             if value].count(os.pardir)

    def fix(match_object):
        """Callback meant to be passed to re.sub"""
        length = len(match_object.group(0))
        title = match_object.group('title')
        link = match_object.group('link')

        link = fixlink(link, level, 'nonhtml', filetype)
        fmt_str = LINK_TEMPLATES[filetype]['format']
        output = fmt_str.format(title=title, link=link)
        if len(output) < length:
            # To ensure that the initial string is replaced by a string of
            # same length to avoid any formatting issues such as in tables.
            title = title + ' ' * (length - len(output))
            output = fmt_str.format(title=title, link=link)
        return output

    def fix_html(match_object):
        start = match_object.group('start')
        link = match_object.group('link')
        end = match_object.group('end')

        link = fixlink(link, level, 'html', filetype)
        fmt_str = LINK_TEMPLATES['html']['format']
        output = fmt_str.format(start=start, link=link, end=end)
        return output

    content = re.sub(LINK_TEMPLATES['html']['regex'], fix_html, content)

    if filetype not in ('md', 'rst'):
        return content

    return re.sub(LINK_TEMPLATES[filetype]['regex'], fix, content)
