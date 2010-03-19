import os

def get_hash_of_file(file, block_size=2**20):
    """
      calculated the hash of a file.
      file: path to file to be hashed
      block_size: a max block size to read at a time
        This is useful for dealing with fs limitations
    """
    import hashlib
    md5 = hashlib.md5()
    open_file = open(file, 'rb')
    while True:
        data = open_file.read(block_size)
        if not data:
            break
        md5.update(data)
    open_file.close()
    return md5.hexdigest()

def detectCPUs():
 """
 Detects the number of CPUs on a system. Cribbed from pp.
 """
 # Linux, Unix and MacOS:
 if hasattr(os, "sysconf"):
     if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
         # Linux & Unix:
         ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
         if isinstance(ncpus, int) and ncpus > 0:
             return ncpus
     else: # OSX:
         return int(os.popen2("sysctl -n hw.ncpu")[1].read())
 # Windows:
 if os.environ.has_key("NUMBER_OF_PROCESSORS"):
         ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
         if ncpus > 0:
             return ncpus
 return 1 # Default


class SignalHandler:
    """
      Class that handles signals.
      Set this as a signal handler via:

      sighand = utilities.SignalHandler
      signal.signal(signal.SIGINT, sighand.exit_handler)

      When the signal is called, it sill set a flag exit_requested
      which the program can query via:

      sighand.is_exit_requested()

      and then exit nicely.
    """
    exit_requested = False
    #@classmethod
    def exit_handler(self, signum, frame):
        print "Process %i: Exit (%i) has been requested..." % \
            (os.getpid(), signum)
        self.exit_requested = True

    #@classmethod
    def is_exit_requested(self):
        return self.exit_requested
    exit_handler = classmethod(exit_handler)
    is_exit_requested = classmethod(is_exit_requested)


