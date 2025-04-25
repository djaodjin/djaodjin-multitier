djaodjin-multitier is a Django application that implements shared tenancy.

Major Features:

  - Dynamically select the following based on subdomain or path prefix:
      * Database connection
      * SMTP connection
      * Templates
  - URL resolvers: Dynamic path prefix (as a hack in i18n module)

The [notes](http://djaodjin.com/blog/multi-tier-implementation-in-django.blog.html)
of the presentation at a SF Django Meetup are useful to understand how
middlewares, thread locals and template loaders were used to implement
multi-tier applications here.

Development
===========

After cloning the repository, create a virtualenv environment, install
the prerequisites, create and load initial data into the database, then
run the testsite webapp.

    $ python -m venv .venv
    $ source .venv/bin/activate
    $ pip install -r testsite/requirements.txt

    # Create the fixtures databases and run the server
    $ make initdb
    $ python manage.py runserver

Release Notes
=============


Tested with

- **Python:** 3.10, **Django:** 4.2 ([LTS](https://www.djangoproject.com/download/))
- **Python:** 3.12, **Django:** 5.1 (next)
- **Python:** 3.7, **Django:** 3.2 (legacy)

0.3.1

 * loads site even when some encrypted database fields cannot be decrypted
 * adds fields for workflow configuration settings
 * swaps order of `location` and `request` parameters in `build_absolute_uri`

[previous release notes](changelog)
