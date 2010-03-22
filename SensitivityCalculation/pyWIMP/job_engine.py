#!/usr/bin/env python
import sys
import os
import optparse
import types
import inspect
import pyWIMP.Calculation.calc_objects as co
from pyWIMP.utilities import utilities
import array
import signal
import errno
import pickle

def job_engine( output_file,\
                num_cpus, \
                num_iter, \
                max_time, \
                model_factory, \
                input_variables):


    """
    ROOT doesn't play well in threads, and so we brute force
    our way out of this by using forks and passing information back and force
    via pipes.  This is the cleanest method because it allows
    each progam to play in its own sandbox without messing with 
    the other processes.  No ROOT objects are loaded until this
    program is forked, which each forked process is completely
    independent.  Random number generators are seeded with TUIDs
    in their respective processes. 
    """

    # Setup: 
    # 
    # Grab the object which will perform the 
    # calculation
   
    # Step 1: Instantiate child processes.  i call them 'threads', but there
    # are actually a forked process.
    thread_list = []
    sighand = utilities.SignalHandler
    for i in range(num_cpus):
        r, w = os.pipe()
        thread_list.append(\
            (r,w,model_factory(w, sighand, num_iter, input_variables)))

    # Step2: Scatter, opening and closing the relevant
    # pipes in the parent and child process
    # now start the threads
    open_threads = []
    print "Scattering %i processes..." % num_cpus
    sys.stdout.flush()
    for read_des,write_des,thread in thread_list:
        pid = os.fork() 
        if pid: # parent
            os.close(write_des)
            read_pipe = os.fdopen(read_des) 
            open_threads.append((pid, read_pipe)) 
        else: # child process
            os.close(read_des)
            thread.run()
            sys.exit(0)
            # stop here for the child process
        
    
    print "Parent (%i) setting signal handlers." % os.getpid()
    signal.signal(signal.SIGINT, sighand.exit_handler)
    signal.signal(signal.SIGALRM, sighand.exit_handler)
    signal.alarm(max_time)
    print "Parent (%i) waiting for processes..." % os.getpid()
    # Parent only
    # Step 3: Gather, sucking on the pipes until close
    # and waiting for all child processes to clean up 
    results_list = [] 
    for pid, read_pipe in open_threads:
        while 1:
            try:
                print "Parent (%i) waiting for process: %i" % (os.getpid(), pid)
                a_list = pickle.loads(read_pipe.read())
                print "Parent (%i) collected for process: %i" % (os.getpid(), pid)
                break
            except IOError, e:
                print "Parent (%i) received signal" % os.getpid()
                if e.args[0] == errno.EINTR:
                    for apid, arp in open_threads:
                        # Make sure they got the signal
                        try:
                            os.kill(apid, signal.SIGUSR1)
                        except: pass
                else: 
                    print "Caught IOError: ", e
                    raise e
                pass
                
        for val in a_list: results_list.append(val)

    signal.alarm(0)
    for i in range(len(open_threads)):
        os.waitpid(-1, 0)
    print "Gathered %i processes." % num_cpus
    if len(results_list) == 0:
        print "No results, exiting."
        return

    # Save the output to a tree
    import ROOT
    print "Writing TTree output."
    open_file = ROOT.TFile(output_file, "recreate")
    output_tree = ROOT.TTree("sensitivity_tree", "sensitivity_tree")

    branch_list = []
    string_list = []
    for key, val in input_variables.items(): 
        # Arg, checking types, shouldn't have to do this 
        root_type = ''
        array_type = ''
        if isinstance(val, types.FloatType): 
            root_type = 'D'
            array_type = 'd'
        elif isinstance(val, types.StringType):
            root_type='string'
            # Do nothing
        else: # Assume integer
            root_type = 'I'
            array_type = 'l'

        if root_type == 'string':
            string_list.append(ROOT.string(val))
            output_tree.Branch(key, string_list[-1])
        else:
            # We have to hold a reference to make sure
            # the array doesn't get killed
            branch_list.append(array.array(array_type, [val]))
            output_tree.Branch(key, \
                               branch_list[-1],\
                               "%s/%s" % (key,root_type))
    modelstring = ROOT.string(model_factory.__name__)
    output_tree.Branch("CalculationName", modelstring)

    # Now we deal with the list output 
    # it is a dictionary, but we don't know the names, or numbers of entries
    # each entry's value, 
    # It is either a ROOT object or a double
    array_dict = {}
    for key, val in results_list[0].items():
        #root_object = False
        #try:
        #    root_object = val.InheritsFrom(ROOT.TObject.Class())
        #except AttributeError: pass
        #if root_object:
        array_dict[key] = array.array('d', [0])
        output_tree.Branch(key, array_dict[key], \
                       "%s/D" % key)

    for dict in results_list:
        for key in dict.keys():
            array_dict[key][0] = dict[key]
        output_tree.Fill()

    output_tree.Write()
    open_file.Close()
    print "Done."
   
if __name__ == "__main__":
    """
    This is the main set of commands called when this python module is executed.
    Following are command line options for the script.
    """

    # Assume the first argument is the 
    # name of the processor to use
    available_models = []
    for name in co.__dict__.keys():
        if name in ['ROOT']: continue # avoid loading ROOT
        if inspect.isclass(getattr(co, name)):
            available_models.append(name) 

    def usage(available_models):
        print 
        print "Available models: "
        for amodel in available_models:
            print "  ", amodel
        print "For help with a particular model, type:"
        print
        print "%s model --help" % sys.argv[0]
        print
        print "Exiting..."

    if (len(sys.argv) < 2):
        usage(available_models)
        sys.exit(1)

    model_name = sys.argv[1]
    if not model_name in available_models:
        print "Error finding model: ", model_name
        usage(available_models)
        sys.exit(1)
    obj_factory = getattr(co, model_name) 
 
    parser = optparse.OptionParser(usage="usage: %prog model [options]")

    # Dynamically set the options for this 
    # particular computation model
    req_items = obj_factory.get_requested_values()
    for key, val in req_items.items():
        found_type = ''
        if isinstance(val[1], types.StringType): 
            found_type = 'string'
        elif isinstance(val[1], types.BooleanType): 
            found_type = 'bool' 
        else:
            found_type = 'float'
        if found_type == 'bool':
            parser.add_option("--%s" % key, dest=key,\
                          help=val[0], \
                          action="store_true",\
                          default=val[1])
        else:
            parser.add_option("--%s" % key, dest=key,\
                          help=val[0], \
                          type=found_type, \
                          default=val[1])

    # Set the other options that we know are required
    parser.add_option("-o", "--output_file", dest="output_file",\
                      help="Define the output file name (full path)",\
                      default="temp.root")
    parser.add_option("-n", "--num_cpus", dest="numprocessors",\
                      help="Define the number of cpus used",\
                      default=utilities.detectCPUs())
    parser.add_option("-a", "--max_time", dest="max_time",\
                      help="Set the max time [seconds] until this program shuts down",\
                      default=0)
    parser.add_option("-i", "--num_iter", dest="num_iter",\
                      help="Number of iterations per cpu",\
                      default=10)

    (options, args) = parser.parse_args()
    
    # Grab the global options
    output_file = options.output_file 
    num_cpus = int(options.numprocessors)
    max_time = int(options.max_time)
    num_iter = int(options.num_iter)

    # Now grab the others
    output_dict = {}
    for key in req_items.keys():
        output_dict[key] = getattr(options, key)
    
    # Give a summary of what was input
    max_string = str(max_time)
    if max_time == 0:
       max_string = "Infinity" 
    output_string = """
Summary:
Calculation:
    """

    for key, val in output_dict.items():
        output_string += """
    %s: %s """ % (req_items[key][0].split('\n')[0], str(val))

    output_string += """

Process:
    Using cpu number: %i
    Iterations on each cpu: %i
    Output file: %s
    Max time (seconds): %s
    """ % ( num_cpus, num_iter, output_file,\
            max_string )

    print output_string
    # Force flush so we only see this once
    sys.stdout.flush()

    # GO
    job_engine(output_file, \
               num_cpus,\
               num_iter,\
               max_time, \
               obj_factory,\
               output_dict)
         
