# Helpers for creating and adding models to the db
#
# Austin Shafer

from srcOptics.models import *

class Creator:
    # ------------------------------------------------------------------
    # DB helper functions
    #
    # Wrappers for adding objects to the database to keep that functionality
    # out of the clone/scanning functions above.

    # ------------------------------------------------------------------
    def create_repo(org_name, repo_url, repo_name, cred):
        org_parent = Organization.objects.get(name=org_name)
        repo_instance,created = Repository.objects.get_or_create(url=repo_url, defaults={'name':repo_name, 'cred':cred})
        return repo_instance

    # ------------------------------------------------------------------
    def create_author(email):
        author_instance,created = Author.objects.get_or_create(email=email)
        return author_instance

    # ------------------------------------------------------------------
    def create_commit(repo_instance, subject, author_instance, sha_, author_date_, commit_date_, added, removed):
        commit_instance,created = Commit.objects.get_or_create(repo=repo_instance, author=author_instance, sha=sha_, commit_date=commit_date_, author_date=author_date_, lines_added=added, lines_removed=removed, subject=subject)
        return commit_instance

    # ------------------------------------------------------------------
    def create_filechange(path, commit, la, lr, binary):
        # find the extension
        split = path.rsplit('.', 1)
        ext = ""
        if len(split) > 1:
            ext = split[1]
                
        #get the file name
        fArray = path.rsplit('/', 1)
        
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

    # ------------------------------------------------------------------
    def create_file(path, commit, la, lr, binary):
        #get the file name
        fArray = path.rsplit('/', 1)
        
        fName = ""
        if len(fArray) > 1:
            fName = fArray[1]
        else:
            fName = fArray[0]

        try:
            file_instance = File.objects.get(path=path)

            # update the lines added/removed
            file_instance.lines_added += int(la)
            file_instance.lines_removed += int(lr)

            file_instance.save()
            return file_instance
            
        except:
            # find the extension
            split = path.rsplit('.', 1)
            ext = ""
            if len(split) > 1:
                ext = split[1]
            
            file_instance = File.objects.create(name=fName, path=path, ext=ext, commit=commit, repo=commit.repo, lines_added=la, lines_removed=lr, binary=binary)
            
            return file_instance
