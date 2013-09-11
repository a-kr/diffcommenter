diffcommenter
=============

A simple webapp for code review.


Requirements
------------

* Python 2.7
* Django 1.5
* psycopg2
* PostgreSQL 9.1
* (optionally) gunicorn

Installation
------------

Create Postgres superuser `da` and database `dc`:

```
sudo -u postgres createuser -s da
createdb -U da dc
```

Clone the repository and initalize the database structure:

```
cd ~
git clone https://github.com/Babazka/diffcommenter.git
cd diffcommenter/diffserver
cp settings_local.example.py settings_local.py
make syncdb
make test
```

### Running the development server

```
make runserver
```

Open http://localhost:8200/ in your browser and see if it works.

### Running with gunicorn

```
make run
make stop
```

The server will run on port 8200.

Usage
-----

Start the diffcommenter server (see above), open the main page in browser and follow the instructions displayed there.




