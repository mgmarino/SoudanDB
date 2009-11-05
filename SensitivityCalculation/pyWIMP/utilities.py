import os

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


class ThreadClass:
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


