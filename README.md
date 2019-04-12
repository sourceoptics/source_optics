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

### Setup

SrcOptics requires some basic structure to be initialized before it can run properly. This can be set up using the `init` management command.

```
python manage.py init -es
```

The `-e` argument automatically creates an admin user and a root organization, along with dropping and recreating the database. This is probably not what you want in a real world application, so omit if if you would like to set things up manually.

* The default Django admin login is `admin`/`password`.

The `-s` argument creates a key for symmetric encryption of login credential passwords. The key location can be configured in the Django settings.

### Adding a repository
Before we can generate statistics we first need to scan the remote repository into our local database. This is done with the `addrepo` management command:

```
python manage.py addrepo -r <repo_url>
python manage.py addrepo -g <github_api_url>
python manage.py addrepo -f <file_name>
```

`addrepo` can accept a single repository URL, a GitHub API endpoint, or a file containing a newline delimited list of repository URLs.

GitHub API URLs can be used for the mass addition of repositories belonging to a user or an organization:
```
python manage.py addrepo -g https://api.github.com/users/<name>/repos
python manage.py addrepo -g https://api.github.com/orgs/<name>/repos
```

You *MUST* scan a repository before generating statistics.

### Aggregating Statistics
```
python manage.py stat <repo_name>
```

Individual repositories can have their statistics aggregated using the `stat` command. This is useful when only one repository should be aggregated, while ignoring the others. Repositories must be enabled before they can be scanned, either by `stat` or by the daemon.

Once `addrepo` and `stat` have been run, you are ready to run the server and view data.


### Running the server
```
python manage.py runserver
```

Defaults to port `8000`. Django admin can be found at `localhost:8000/admin`.

### Running the scanner daemon
```
# This will run until killed
python manage.py scan
```

SrcOptics provides a daemon job for automatically keeping repositories and their statistics up to date. This daemon will continue to pull new remote data and scan new unprocessed commits. It is recommended to add

### Postgresql Setup

For a complete setup guide to postgresql setup please refer to an operating system specific guide. Usually you have  to enable postgres and initialize the database directory before it can be used.

The default name of the database used is called `srcopt`. For things to run smoothly you must first create a role for the unix user you wish to run srcOptics as. The role needs to have createdb permissions along with ownership of the `srcopt` database.

```
srcopt=CREATE ROLE <username> [ [ WITH ] option [ ... ] ]

-- may also need --
srcopt=# alter user <username> createdb;
ALTER ROLE
srcopt=# ALTER DATABASE srcopt OWNER TO <username>;
ALTER DATABASE
```

### Dev info / Random tips

* Run `sass --watch --no-source-map --style compressed srcOptics/static/_scss:srcOptics/static` during development to build css files
  * If you use macports, the `sass` utility is not installed, only the raw compiler `sassc`. Here is a hacky one liner you can use to create main.css with only `sassc`:

```
cat srcOptics/static/_scss/main.scss srcOptics/static/_scss/*.scss | sassc -I srcOptics/static/_scss --style compressed -s > srcOptics/static/main.css
```

* Like most Django projects, the `settings.py` file contains many useful variables for configuring srcOptics. These should all be heavily commented

* Django 1.11 has a different include path for `urls`, which will cause an exception when trying to load `urls.py`. Use Django 2.0 or higher to avoid differences such as this.
