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

    $ virtualenv _installTop_
    $ source _installTop_/bin/activate
    $ pip install -r testsite/requirements.txt
    $ make initdb
    $ python manage.py runserver
