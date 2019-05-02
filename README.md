# SrcOptics

SrcOptics is a repository analysis tool designed to visualize committer trends in a repository. Users can `scan` a repository to import its data into the local database, and `aggregate` time interval statistics to be presented in multiple formats.

One of the primary goals of srcOptics is to track community or team involvement within a project. It can display information based on version control metadata, including:
* Statistics over time, for both repositories and individual authors.
  * Total Commits
  * Lines Added
  * Lines Removed
  * Total Authors
  * Total Files
* Top authors for a repository based on a time range.
* Tabular or graphical comparison of all repositories.
* Average commits per day.
* Author activity across all repositories.

SrcOptics is perfect for monitoring the health of an open source, corporate, or academic codebase. This project originated in the Senior Design Center at North Carolina State University. It was designed to allow teaching staff to quickly view multiple student repositories and discern if a team is productive or in need of assistance.

## Installation Instructions At A Glance

```
# not shown here: install git/python3/postgresql/pip with default package manager

# initialize and start postgres
service postgresql initdb
service postgresql start

# get the code
git clone https://github.ncsu.edu/engr-csc-sdc/2019SpringTeam02.git
cd 2019SpringTeam02

## set up the application
mkdir /etc/srcoptics
pip install -r requirements.txt

# create a role for whatever <username> you would like to run srcOptics as
sudo -u postgres createuser --createdb <username>
python manage.py init -s

# scan a repository into the system
python manage.py addrepo -r <repo_url>

# aggregate statistics for that repo
python manage.py stat <repo_name>

# run the application on port 8000
python manage.py runserver 0:8000
```

Details about these commands can be found in their corresponding sections below.

## Getting Started
This guide will instruct you on how to have a working srcOptics app on your system, along with a general guide as to where specific functionality can be located.

The general per-repository workflow is as follows:
* *Scan* a repository to import version control metadata into postgresql.
  * Uses the `addrepo` command
* *Aggregate* time-interval statitics for a repository.
  * Uses the `stat` command

Both of these tasks are encapsulated by the daemon provided. Scanning _Must_ take place before aggregation, or else there is no repository to aggregate. Once there are statistics aggregated information can be displayed by the Django server.

### Dependencies
The following should be installed using a package manager such as Homebrew or Aptitude:
- Git
- Pip
- Python 3.6+
- PostgreSQL (with CLI)

### Installing Dependencies
Run `pip install -r requirements.txt` to install required modules.

### Postgresql Setup

Before any databases can be created, postgresql must be initialized:
* rc.d style: `service postgresql initdb`.
* systemd: `postgresql-setup initdb`

The default name of the database used is called `srcopt`. It is created using the `init` command. For things to run smoothly you must first create a role for the unix user you wish to run srcoptics as. The role needs to have createdb permissions along with ownership of the `srcopt` database.

```
# Run before creating a new database
sudo -u postgres createuser --createdb <username>

# To add a new user to an existing database:
CREATE ROLE <username> WITH CREATEDB SUPERUSER;
ALTER DATABASE srcopt OWNER TO <username>;
```
`createuser` must be run as the default postgresql user. On some systems this is `postgres`, and on others it is `pgsql`.

For more roles, please refer to the [documentation](https://www.w3resource.com/PostgreSQL/postgresql-database-roles.php)

### Initialization

SrcOptics requires some basic objects to be initialized before it can run properly. This can be set up using the `init` management command.

```
python manage.py init -s
```

This will create the default database (default name is 'srcopt'), perform migrations, and initialize a root organization. Both of these steps are required for srcoptics to run. `init` will also prompt the user for a username and password for a new superuser.

The `-s` argument creates a key for symmetric encryption of login credential passwords. The key location can be configured in the Django settings. This only needs to be used the first time. It will not delete any existing keys it finds. The default location is `/etc/srcoptics/*`, the user running srcoptics needs to have write permissions to this directory.

```
mkdir /etc/srcoptics
```

### Management Commands Overview

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

Defaults to port `8000`. Django admin can be found at `localhost:8000/admin`. It is recommended to add repositories in Django Admin and let the scanner/aggregator daemon automatically keep things up to date.

### Running the scanner daemon
```
# This will run until killed
python manage.py scan
```

SrcOptics provides a daemon job for automatically keeping repositories and their statistics up to date. This daemon will continue to pull new remote data and scan new unprocessed commits. It is recommended to add

## Developer Info

Modifying srcOptics is a familiar experience to those who have used Django before. In general the code is well commented, although there are a few remaining organizational issues. Please feel free to submit any pull requests you may have.

### Project Heirarchy
Some of the notable code locations:
* `config`: Holds Django Settings
* `srcOptics/models`: Django models for postgresql backend.
* `srcOptics/management/commands`: Django management commands such as init, addrepo, etc.
* `srcOptics/scanner`: The repository scanner. Also holds the daemon implementation.
* `srcOptics/stats`: The statistic aggregator. This can be found in `rollup.py`.
  * The term Rollup is the same thing as Aggregation.
* `srcOptics/tests`: Django tests can be run with `python manage.py test`
* `srcOptics/views`: The index, repository, and author pages.
  * The `graphs` directory holds implementations of various repository or author specific graphs
* `srcOptics/templates`: Django templates used to generate webpages. Used by the views code
* `srcOptics/static/_scss`: SASS sytesheets which are compiled into CSS. See the Random tips section for more.
* `srcOptics/create.py`: Helper methods to create model objects.
  * This will eventually be moved into the individual model classes.

### Random tips

* SCSS file must be compiled into CSS for changes to take effect.
  * Use `sass --watch --no-source-map --style compressed srcoptics/static/_scss:srcoptics/static` to generate css files.

If your package manager does not install the `sass` utility, the raw `sassc` compiler can be used. Here is a hacky one liner you can use to create main.css with only `sassc`:
```
cat srcoptics/static/_scss/main.scss srcoptics/static/_scss/*.scss | sassc -I srcoptics/static/_scss --style compressed -s > srcoptics/static/main.css
```

* Like most Django projects, the `settings.py` file contains many useful variables for configuring srcoptics. These should all be heavily commented. Future support for Django split settings will be added.

* Django 1.11 has a different include path for `urls`, which will cause an exception when trying to load `urls.py`. Use Django 2.0 or higher to avoid differences such as this.
