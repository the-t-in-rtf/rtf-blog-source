#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Tony Atkins <tony@raisingthefloor.org>'
SITENAME = u'The "T" in RtF'
SITEURL = 'http://the-t-in-rtf.github.io'

TIMEZONE = 'Europe/Amsterdam'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
LINKS =  (('Fluid Project Blog', 'http://fluidproject.org/blog/'),
          ('Cloud4All Blog', 'http://blogs.cloud4all.info/'),)

# Social widget
SOCIAL = (('twitter', 'https://twitter.com/duhrer'),
          ('linkedin', 'http://www.linkedin.com/profile/view?id=31505257'),
          ('github', 'http://github.com/the-t-in-rtf/'),)

DEFAULT_PAGINATION = 10

THEME = 'pelican-bootstrap3'

DISQUS_SITENAME = 'thetinrtf'

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
