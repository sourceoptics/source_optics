#  Copyright 2018-2019, Michael DeHaan LLC
#  License: Apache License Version 2.0
#  -------------------------------------------------------------------------
#  ssh_agent.py - processes are to be run wrapped by 'ssh-agent' processes
#  and the workers can use SSH keys configured per project to do SCM checkouts
#  or use SSH-based automation. This is mostly handled right now
#  through basic expect scripts
#  --------------------------------------------------------------------------

import os
import tempfile
from . import commands

# =============================================================================

class SshAgentManager(object):

    def __init__(self):
        self.tempfile_paths = []

    def add_key(self, repo, cred):

        (_, keyfile) = tempfile.mkstemp()
        answer_file = None

        try:
            fh = open(keyfile, "w")
            private = cred.unencrypt_ssh_private_key()
            for line in private.splitlines():
                line = line.rstrip()
                fh.write(line)
                fh.write("\n")
            fh.close()

            answer_file = None

            if cred.ssh_unlock_passphrase:
                passphrase = cred.unencrypt_ssh_unlock_passphrase()
                self.ssh_add_with_passphrase(repo, keyfile, passphrase)
            else:
                if ',ENCRYPTED' in private:
                    # FYI: this seemingly may not always occur with locked keys
                    raise Exception("SSH key has a passphrase but an unlock password was not set. Aborting")
                self.ssh_add_without_passphrase(repo, keyfile)
        finally:
            os.remove(keyfile)
            if answer_file:
                os.remove(answer_file)
            pass

    def cleanup(self, repo):
        """
        remove all SSH identities
        """
        print("removing SSH identities")
        commands.execute_command(repo, "ssh-add -D", log=False)

    def ssh_add_without_passphrase(self, repo, keyfile):
        print(keyfile)
        cmd = "ssh-add %s < /dev/null" % keyfile
        commands.execute_command(repo, cmd, env=None, log=False)

    def ssh_add_with_passphrase(self, repo, keyfile, passphrase):
        (_, fname) = tempfile.mkstemp()
        fh = open(fname, "w")
        script = """
        #!/usr/bin/expect -f
        spawn ssh-add %s
        expect "Enter passphrase*:"
        send "%s\n";
        expect "Identity added*"
        interact
        """ % (keyfile, passphrase)
        fh.write(script)
        fh.close()
        commands.execute_command(repo, "/usr/bin/expect -f %s" % fname, log=False)
        os.remove(fname)
        return fname