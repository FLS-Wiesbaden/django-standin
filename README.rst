=====
Standin plan
=====

Standin plan is a Django app to provide a standin plan for schools (whatever kind of school). 

The application is published as GPL v3 as it should be free and open for all schools and every school should be able to take benefit of others improvements. For us and our children. 

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "standin" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'standin',
    ]

2. Include the standin URLconf in your project urls.py like this::

    url(r'^standin/', include('standin.urls')),

3. Run `python manage.py migrate` to create the standin models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create entries (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/standin/ to see the plan or http://127.0.0.1:8000/standin/teacher for the teacher plan!

