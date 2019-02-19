# SrcOptics               
## Developer's guide
This guide will instruct you on how to have a working Django app on your system

### Prerequisites
- Git
- Pip
- Python 3.6+
- PostgreSQL (with CLI)

### Installation
Run `pip install -r requirements.txt` to install required modules.

### Running the server
Run `python manage.py runserver`

### Dev info
To initialize the DB with a root organization and a Django admin account, run `python manage.py init` (use -e flag to default to admin/password) 

Run `sass --watch --no-source-map --style compressed srcOptics/static/_scss:srcOptics/static` during development to build css files