import os

class Repository:
    def clone_repo(repo_url):
        work_dir = os.path.abspath(os.path.dirname(__file__).rsplit("/", 2)[0]) + '/work'
        os.system('mkdir -p ' + work_dir)
        repo_name = repo_url.rsplit('/', 1)[1]
        print('git clone ' + repo_url + ' ' + work_dir)
        os.system('git clone ' + repo_url + ' ' + work_dir + '/' + repo_name)
