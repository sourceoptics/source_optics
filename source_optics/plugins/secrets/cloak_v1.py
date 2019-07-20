#  Copyright 2018, Michael DeHaan LLC
#  License: Apache License Version 2.0
#  -------------------------------------------------------------------------
#  basic.py - this is a cloaking plugin for symetric encryption of secrets.
#  it's not intended to be a fortress but for the implementation to use
#  when you're not using something more complex.  It is versioned by implementation
#  classes so the plugin can support improvements in existing cloaked secrets
#  when required.
#  --------------------------------------------------------------------------

from django.conf import settings
from cryptography import fernet
import binascii

class BasicV1(object):

    HEADER = "[SRCOPT-CLOAK][BASIC][V1]"

    def __init__(self):
        pass

    def get_key(self):
        symmetric = settings.SYMMETRIC_SECRET_KEY
        fh = open(symmetric, 'rb')
        data = fh.read()
        fh.close()
        return data

    def cloak(self, msg):
        symmetric = self.get_key()
        ff = fernet.Fernet(symmetric)
        msg = msg.encode('utf-8')
        encrypted = ff.encrypt(msg)
        printable = binascii.hexlify(encrypted).decode('ascii')
        versioned = "%s%s" % (self.HEADER, printable)
        return versioned

    def decloak(self, msg):
        symmetric = self.get_key()
        ff = fernet.Fernet(symmetric)
        encrypted = msg.replace(self.HEADER, "", 1)
        unencrypted = ff.decrypt(encrypted)
        printable = binascii.unhexlify(unencrypted)
        # print("DECODED: %s" % printable)
        return printable


class Plugin(object):

    HEADER = "[SRCOPT-CLOAK][BASIC]"

    def __init__(self):
        pass

    def implementation_for_version(self, msg):
        if msg.startswith(BasicV1.HEADER):
            return BasicV1()
        raise Exception("unknown cloaking version")

    def cloak(self, msg):
        return BasicV1().cloak(msg)

    def decloak(self, msg):
        impl = self.implementation_for_version(msg)
        return impl.decloak(msg)

    def recognizes(self, msg):
        if settings.SYMMETRIC_SECRET_KEY is None:
            # user didn't run 'make secrets' yet, so disable the plugin
            return False
        return msg.startswith(self.HEADER)

