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

# =============================================================================

class SshAgentManager(object):

    def __init__(self):
        self.tempfile_paths = []

    def add_key(self, cred):

        (_, keyfile) = tempfile.mkstemp()
        answer_file = None

        try:
            fh = open(keyfile, "w")
            private = cred.get_private_key()
            fh.write(private)
            fh.close()

            answer_file = None

            if cred.unlock_password:
                LOG.debug("adding SSH key with passphrase!")
                self.ssh_add_with_passphrase(keyfile, access.get_unlock_password())
            else:
                if ',ENCRYPTED' in private:
                    raise Exception("SSH key has a passphrase but an unlock password was not set. Aborting")
                LOG.debug("adding SSH key without passphrase!")
                self.ssh_add_without_passphrase(keyfile)
        finally:
            os.remove(keyfile)
            if answer_file:
                os.remove(answer_file)

    def cleanup(self):
        # remove SSH identities
        print("removing SSH identities")
        commands.execute_command(self.build, "ssh-add -D", log_command=False, message_log=False, output_log=False)

    def ssh_add_without_passphrase(self, keyfile):
        print(keyfile)
        cmd = "ssh-add %s < /dev/null" % keyfile
        commands.execute_command(self.build, cmd, env=None, log_command=False, message_log=False, output_log=False)

    def ssh_add_with_passphrase(self, keyfile, passphrase):
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
        commands.execute_command(self.build, "/usr/bin/expect -f %s" % fname, output_log=False, message_log=False)
        os.remove(fname)
        return fname