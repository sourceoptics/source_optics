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

### Dev info / Random tips

* Run `sass --watch --no-source-map --style compressed srcOptics/static/_scss:srcOptics/static` during development to build css files

* Like most Django projects, the `settings.py` file contains many useful variables for configuring srcOptics. These should all be heavily commented