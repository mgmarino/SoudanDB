#!/usr/bin/env python
try:
    import ROOT
    import sys
    import os
    import array
    import optparse
    import signal
    import errno
    import pickle
except ImportError:
    print "Error importing"
    raise 

absolute_path = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) )
sys.path.append(absolute_path)

try:
    from pyWIMP.calc_objects import calculate_object_factory 
    from utilities import utilities
except ImportError:
    raise
def main( total_time, \
          threshold, \
          energy_max, \
          kilograms, \
          background_rate, \
          wimp_mass, \
          output_file,\
          number_iterations, \
          cl, \
          num_cpus, \
          max_time, \
          model_name, \
          constant_time, \
          constant_energy):


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
    obj_factory = calculate_object_factory(model_name)
    if not obj_factory:
        print "Error finding model: ", model_name
        print "Exiting..."
        return
    
    # Step 1: Instantiate child processes.  i call them 'threads', but there
    # are actually a forked process.
    thread_list = []
    sighand = utilities.SignalHandler
    for i in range(num_cpus):
        r, w = os.pipe()
        thread_list.append(\
            (r,w,obj_factory( total_time, threshold, energy_max, \
             kilograms, background_rate, wimp_mass, \
             number_iterations, cl, constant_time, \
             constant_energy, w, sighand)))

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
    print "Writing TTree output."
    open_file = ROOT.TFile(output_file, "recreate")
    output_tree = ROOT.TTree("sensitivity_tree", "sensitivity_tree")

    total_time_out = array.array('d', [total_time]) 
    threshold_out = array.array('d', [threshold]) 
    energy_max_out = array.array('d', [energy_max]) 
    mass_of_detector_out = array.array('d', [kilograms]) 
    background_rate_out = array.array('d', [background_rate]) 
    wimp_mass_out = array.array('d', [wimp_mass]) 
    model_amplitude_out = array.array('d', [0]) 
    cross_section_out = array.array('d', [0]) 
    likelihood_max_out = array.array('d', [0]) 
    final_likelihood_max_out = array.array('d', [0]) 
    modelstring = ROOT.string(model_name)

    output_tree.Branch("CalculationName", modelstring)
    output_tree.Branch("total_time", total_time_out, "total_time/D")
    output_tree.Branch("threshold", threshold_out, "threshold/D")
    output_tree.Branch("energy_max", energy_max_out, "energy_max/D")
    output_tree.Branch("mass_of_detector", mass_of_detector_out, \
                       "mass_of_detector/D")
    output_tree.Branch("background_rate", background_rate_out, \
                       "background_rate/D")
    output_tree.Branch("wimp_mass", wimp_mass_out, "wimp_mass/D")

    # Now we deal with the list output 
    # it is a dictionary, but we don't know the names, or numbers of entries
    # each entry's value, though is a double
    array_dict = {}
    for key in results_list[0].keys():
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
    parser = optparse.OptionParser()
    parser.add_option("-n", "--num_processors", dest="numprocessors",\
                      help="Define the number of processors", \
                      default=utilities.detectCPUs())
    parser.add_option("-T", "--total_time", dest="total_time",\
                      help="Defines the total time in years",\
                      default=5)
    parser.add_option("-t", "--threshold", dest="threshold",\
                      help="Define the threshold",\
                      default=0)
    parser.add_option("-e", "--energy_max", dest="energy_max",\
                      help="Define the maximum_energy",\
                      default=80)
    parser.add_option("-m", "--detector_mass", dest="detector_mass",\
                      help="Define the detector total mass in kg",\
                      default=10)
    parser.add_option("-r", "--background_rate", dest="background_rate",\
                      help="Define the background rate in counts/kg/keV/day",\
                      default=0.01)
    parser.add_option("-w", "--wimp_mass", dest="wimp_mass",\
                      help="Define the wimp mass in GeV",\
                      default=10)
    parser.add_option("-o", "--output_file", dest="output_file",\
                      help="Define the output file name (full path)",\
                      default="temp.root")
    parser.add_option("-d", "--model", dest="model_name",\
                      help="Define the calculation model to use",\
                      default="WIMPModel")
    parser.add_option("-i", "--num_iter", dest="num_iter",\
                      help="Define the number of iterations",\
                      default=10)
    parser.add_option("-c", "--confidence_level", dest="confidence_level",\
                      help="Define the CL of the calculation",\
                      default=0.9)
    parser.add_option("-a", "--max_time", dest="max_time",\
                      help="Set the max time [seconds] until this program shuts down",\
                      default=0)
    parser.add_option("--constant_time", action="store_true", \
                      dest="constant_time",\
                      help="Integrate over time, do not fit over time",\
                      default=False)
    parser.add_option("--constant_energy", action="store_true", \
                      dest="constant_energy",\
                      help="Integrate over energy, do not fit over energy",\
                      default=False)


    (options, args) = parser.parse_args()
    total_time = float(options.total_time)
    threshold = float(options.threshold)
    energy_max = float(options.energy_max)
    kilograms = float(options.detector_mass)
    background_rate = float(options.background_rate) # units of counts/keV/kg/d
    wimp_mass = float(options.wimp_mass) # units of GeV
    output_file = options.output_file # units of GeV
    num_cpus = int(options.numprocessors)
    num_iter = int(options.num_iter)
    cl = float(options.confidence_level)
    max_time = int(options.max_time)
    constant_time = options.constant_time
    constant_energy = options.constant_energy
    model_name = options.model_name

    if cl >= 1:
        print "CL ERROR > 1"
        sys.exit(1)

    max_string = str(max_time)
    if max_time == 0:
       max_string = "Infinity" 
    print """
Summary:
Calculation:
    Threshold: %g keV
    Maximum Energy: %g keV
    Mass of Detector(s): %g kg
    Background Rate: %g counts/keV/kg/d
    Mass of Wimp: %g GeV
    Total time: %g years
    Constant Time: %s
    Constant Energy: %s
    CL: %g 
    Model name: %s

Process:
    Using cpu number: %i
    Iterations on each cpu: %i
    Output file: %s
    Max time (seconds): %s
    """ % ( threshold, energy_max, \
            kilograms, background_rate,\
            wimp_mass, total_time, str(constant_time),\
            str(constant_energy), cl, model_name,\
            num_cpus, num_iter, output_file,\
            max_string )

    # Force flush so we only see this once
    sys.stdout.flush()
    # GO
    main(total_time, \
         threshold, \
         energy_max, \
         kilograms, \
         background_rate, \
         wimp_mass, \
         output_file, \
         num_iter, \
         cl, \
         num_cpus,\
         max_time, \
         model_name,\
         constant_time, \
         constant_energy)
