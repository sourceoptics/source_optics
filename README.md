# SrcOptics               
## Developer's guide
This guide will instruct you on how to have a working Django app on your system

### Dependencies
- Git
- Pip
- Python 3.6+
- PostgreSQL (with CLI)

### Installation
Run `pip install -r requirements.txt` to install required modules.

### Setup

SrcOptics requires some basic structure to be initialized before it can run properly. This can be set up using the `init` management command.

```
python manage.py init -s
```

This will create the default database (default name is 'srcopt'), perform migrations, and initialize a root organization. Both of these steps are required for srcoptics to run. `init` will also prompt the user for a username and password for a new superuser. 

The `-s` argument creates a key for symmetric encryption of login credential passwords. The key location can be configured in the Django settings. This only needs to be used the first time. It will not delete any existing keys it finds. The default location is `/etc/srcoptics/*`, the user running srcoptics needs to have write permissions to this directory.


### Management Commands

Management commands can be run with `python manage.py <command_name>`

| Command       | Summary           | 
| ------------- |:-------------:|
| init		| set up database resources and perform migrations |
| runserver	| run the webserver |
| addrepo	| pull remote repositories and scan them into the database |
| stat		| aggregate statistics for a _single_ repository |
| scan		| run the scanning and aggregation daemon  |

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

Before any databases can be created, postgresql must be initialized:
* rc.d style: `service postgresql initdb`.
* systemd: `postgresql-setup initdb`

The default name of the database used is called `srcopt`. It is created using the `init` command. For things to run smoothly you must first create a role for the unix user you wish to run srcoptics as. The role needs to have createdb permissions along with ownership of the `srcopt` database.

```
CREATE ROLE <username> WITH CREATEDB SUPERUSER;
ALTER DATABASE srcopt OWNER TO <username>;
```
For more roles, refer to the [documentation](https://www.w3resource.com/PostgreSQL/postgresql-database-roles.php)

### Dev info / Random tips

* SCSS file must be compiled into CSS for changes to take effect.
  * Run `sass --watch --no-source-map --style compressed srcoptics/static/_scss:srcoptics/static` during development to build css files
  * If you use macports, the `sass` utility is not installed, only the raw compiler `sassc`. Here is a hacky one liner you can use to create main.css with only `sassc`:

```
cat srcoptics/static/_scss/main.scss srcoptics/static/_scss/*.scss | sassc -I srcoptics/static/_scss --style compressed -s > srcoptics/static/main.css
```

* Like most Django projects, the `settings.py` file contains many useful variables for configuring srcoptics. These should all be heavily commented

* Django 1.11 has a different include path for `urls`, which will cause an exception when trying to load `urls.py`. Use Django 2.0 or higher to avoid differences such as this.
