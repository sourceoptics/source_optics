# Helpers for creating and adding models to the db
#
# Austin Shafer

from srcOptics.models import *

# FIXME: move these into class methods on the model objects

class Creator:

    # ------------------------------------------------------------------
    # DB helper functions
    #
    # Wrappers for adding objects to the database to keep that functionality
    # out of the clone/scanning functions above.

    # ------------------------------------------------------------------
    def create_repo(org_name, repo_url, repo_name, cred):
        org_parent = Organization.objects.get(name=org_name)
        #Removed name argument so that user can specify arbitrary repo name
        repo_instance,created = Repository.objects.get_or_create(organization=org_parent, url=repo_url, name=repo_name, defaults={'cred':cred})
        return repo_instance

    # ------------------------------------------------------------------
    def create_author(email, repo):
        author_instance,created = Author.objects.get_or_create(email=email)
        # FIXME: probably should avoid calling .save() if already there w/ correct relations
        author_instance.repos.add(repo)
        author_instance.save()
        return author_instance

    # also return if created so that the scanner can determine if we have
    # processed this commit before. It should check if created is false
    # ------------------------------------------------------------------
    def create_commit(repo_instance, subject, author_instance, commit_sha, adate, cdate, added, removed):
        commit_instance,created = Commit.objects.get_or_create(sha=commit_sha,
                                                               defaults={
                                                                   'subject':subject,
                                                                   'repo':repo_instance,
                                                                   'author':author_instance,
                                                                   'author_date':adate,
                                                                   'commit_date':cdate,
                                                                   'lines_added':added,
                                                                   'lines_removed':removed})

        return (commit_instance, created)

    # ------------------------------------------------------------------
    def create_filechange(path, commit, la, lr, binary):
        # find the extension
        (root, ext) = os.path.splitext(path)

        #get the file name
        fArray = os.path.basename(path)

        fName = ""
        if len(fArray) > 1:
            fName = fArray[1]
        else:
            fName = fArray[0]

        filechange_instance = FileChange.objects.create(name=fName, path=path, ext=ext, commit=commit, repo=commit.repo, lines_added=la, lines_removed=lr, binary=binary)

        # add the file change to the global file object
        file_instance = File.objects.get(name=fName, path=path)
        file_instance.changes.add(filechange_instance)
        file_instance.save()

        return filechange_instance

    # This assumes that commits (and their effect on files) will not be processed
    # more than once. It is on the scanner (the caller) to never scan commits
    # more than once.
    # ------------------------------------------------------------------
    def create_file(path, commit, la, lr, binary):
        file_instance = {}
        #get the file name
        fArray = os.path.basename(path)

        fName = ""
        if len(fArray) > 1:
            fName = fArray[1]
        else:
            fName = fArray[0]

        # find the extension
        (root, ext) = os.path.splitext(path)

        # update the global file object with the line counts
        file_instance,created = File.objects.get_or_create(path=path, defaults={
                    "lines_added":int(la),
                    "lines_removed":int(lr),
                    "name":fName,
                    "commit":commit,
                    "repo":commit.repo,
                    "binary":binary,
                    "ext":ext})

        # update the la/lr if we found the file
        if not created:
                file_instance.lines_added += int(la)
                file_instance.lines_removed += int(lr)
                file_instance.save()

        # add the la/lr to the commit for its total count
        commit.lines_added += int(la)
        commit.lines_removed += int(lr)
        commit.files.add(file_instance)
        commit.save()
        return file_instance

    # FIXME: eliminate this function
    def create_total_rollup(start_date=None, interval=None, repo=None, lines_added=None, lines_removed=None,
                            lines_changed=None, commit_total=None, files_changed=None, author_total=None, total_instances=None):
        total_instances.append(Statistic(start_date = start_date, interval = interval, repo = repo, lines_added = lines_added,
            lines_removed = lines_removed, lines_changed = lines_changed, commit_total = commit_total, files_changed = files_changed,
            author_total = author_total))

    # FIXME: this should all use keyword arguments
    def create_author_rollup(start_date, interval, repo, author, lines_added, lines_removed,
                            lines_changed, commit_total, files_changed, author_instances):
        author_instances.append(Statistic(start_date = start_date, interval = interval, repo = repo, author=author, lines_added = lines_added,
        lines_removed = lines_removed, lines_changed = lines_changed, commit_total = commit_total, files_changed = files_changed))


