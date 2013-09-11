diffcommenter
=============

A simple webapp for code review.


Requirements
------------

* Python 2.7
* Django 1.5
* PostgreSQL 9.1

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
make syncdb
make test
```

Run the development server:
```
make run
```

Open http://localhost:8200/ in your browser and see if it works.




