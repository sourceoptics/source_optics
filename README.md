# SrcOptics               
## Developer's guide
This guide will instruct you on how to have a working Django app on your system

### Prerequisites
- Pip
- Python 3.6+
- PostgreSQL

### Installation
Run `pip install -r requirements.txt`

### Running the server
Run `python manage.py runserver`

### Custom management commands
`python manage.py`
    `addrepo [repo_url]`
    `addstat [repo_name]`
    `scan [-r] [--recursive] [-s] [--store]`
    `stat`
