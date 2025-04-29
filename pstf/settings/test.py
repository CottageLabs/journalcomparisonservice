from .base import *

DEBUG = True

ALLOWED_HOSTS = ['pstf.cottagelabs.com']

# Because NGINX is sitting in front it will relay the original request scheme
# see deploy/nginx/test.conf
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Unnecessary to make Django force HTTPS as nginx is sitting in front and
# already does that
# SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 3600  # One hour
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True