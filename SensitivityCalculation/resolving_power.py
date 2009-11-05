#!/usr/bin/env python
try:
    import ROOT
    import math
    import sys
    import os
    import array
    import optparse
    from wimp_model import AllWIMPModels
    import signal
    import errno
except ImportError:
    print "Error importing"
    raise 
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

exit_requested = False

def exit_handler(signum, frame):
    global exit_requested
    print "Process %i: Exit (%i) has been requested..." % (os.getpid(), signum)
    exit_requested = True

class CalculateObject:
    """
    Class handles performing a sensitivity calculation
    for a Ge detector given the input parameters.
    FixME: This class uses AllWIMPModels class, but doesn't
    allow an interface to change those values.
    """
    def __init__(self, total_time, \
          threshold, energy_max, kilograms, \
          background_rate, wimp_mass, \
          number_iterations, cl,\
          constant_time, constant_energy, \
          output_pipe):
        self.total_time = total_time
        self.threshold = threshold
        self.energy_max = energy_max
        self.kilograms = kilograms
        self.background_rate = background_rate
        self.wimp_mass = wimp_mass
        self.number_iterations = number_iterations
        self.cl = cl
        self.constant_time = constant_time
        self.constant_energy = constant_energy
        self.output_pipe = output_pipe
        self.exit_now = False


    def run(self):
        """
        Do the work.  Perform the fits, and return the results
        """
        ROOT.gROOT.SetBatch()
        wimpClass = AllWIMPModels(time_beginning=0, \
            time_in_years=self.total_time, \
            energy_threshold=self.threshold, \
            energy_max=self.energy_max,\
            mass_of_wimp=self.wimp_mass)
 
        ROOT.RooRandom.randomGenerator().SetSeed(0)
        ROOT.RooMsgService.instance().setSilentMode(True)
        ROOT.RooMsgService.instance().setGlobalKillBelow(3)

        # Open the pipe to write back on
        write_pipe = os.fdopen(self.output_pipe, 'w') 

        total_counts = int(self.kilograms*self.background_rate*\
            (self.energy_max-self.threshold)*\
            self.total_time*365)

        # which variables we care about
        variables = ROOT.RooArgSet()
        if self.constant_time:
            wimpClass.get_time().setVal(0)
            wimpClass.get_time().setConstant(True)
        else:
            variables.add(wimpClass.get_time())
        if not self.constant_energy:
            variables.add(wimpClass.get_energy())

        # This is where we define our models
        flat_function =  wimpClass.get_flat_model()
        #pdf = wimpClass.get_WIMP_model(wimp_mass)
        #pdf = wimpClass.get_simple_model()
        #pdf = wimpClass.get_WIMP_model_with_escape_vel_no_ff(wimp_mass)
        model = wimpClass.get_WIMP_model_with_escape_vel(wimp_mass)
        norm = wimpClass.get_normalization().getVal()

        # Set the numeric integration properties, this is important
        # since some of these integrals are difficult to do
        precision = ROOT.RooNumIntConfig.defaultConfig()
        precision.setEpsRel(1e-8)
        precision.setEpsAbs(1e-8)
        precision.method2D().setLabel("RooIntegrator2D")

        # Now perform the integral
        norm_integral_val = model.createIntegral(variables).getVal()
        # This integral is in units of pb^{-1} kg^{-1} yr d^{-1}
        if norm_integral_val == 0.0:
            print "Integral defined as 0, meaning it is below numerical precision"
            print "Aborting further calculation"
            write_pipe.write(str([]))
            write_pipe.close()
            return
        final_function = model
        # now the mult factor is in units of pb which is what we want
        mult_factor = norm#/(norm_integral_val*kilograms*time_factor) 
 
        flat_normal = ROOT.RooRealVar("flat_normal", "flat_normal", total_counts, 0, 3*total_counts)
        model_normal = ROOT.RooRealVar("model_normal", "model_normal", 1, 0, 100000)
        model_extend = ROOT.RooExtendPdf("model_extend", "model_extend", model, model_normal)
        flat_extend = ROOT.RooExtendPdf("flat_extend", "flat_extend", flat_function, flat_normal)
        added_pdf = ROOT.RooAddPdf("add_pdf", "add_pdf", ROOT.RooArgList(flat_extend, model_extend))
        
        # Set up signal handler
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGUSR1, exit_handler)

        results_list = self.scan_confidence_value_space_for_model(added_pdf, flat_function, model_normal, \
                                              mult_factor, variables, total_counts, \
                                              self.number_iterations, self.cl)

        write_pipe.write(str(results_list))
        write_pipe.close()


    def find_confidence_value_for_model(self, model, data, \
                                        model_normal, \
                                        conf_level, \
                                        mult_factor, \
                                        tolerance = 0.001):
    
        global exit_requested
        retry_error = (0,0,0,0)
        # Error check
        if conf_level < 0:
            print "Error, CL must be greater than 0"
            return None
    
        # First ML fit, let everything float
        model_normal.setConstant(False)
        model_normal.setVal(1)
        result = model.fitTo(data, ROOT.RooFit.Save(True),\
                                   ROOT.RooFit.PrintLevel(-1),\
                                   ROOT.RooFit.Verbose(False),\
                                   ROOT.RooFit.Hesse(False),\
                                   ROOT.RooFit.Minos(False))#,\
    
        # Check fit status
        if result.status() != 0: 
            print "Possible error in status"
            result.IsA().Destructor(result)
            return retry_error 
    
        minimized_value = model_normal.getVal()
        orig_Nll = -result.minNll()
        new_minNll = orig_Nll 
    
        # IMPORTANT
        # Sometimes, ROOT and python don't play well
        # together wrt memory handling.  ROOT expects
        # the "result" to be owned by the caller of the 
        # function, but python doesn't clean it up
        # automatically.  This is a problem since this
        # function performs *a lot* of fits.  You will
        # take down the machine if you do not clean them up,
        # I almost took down Athena.  -mgm-
        # Manually cleanning up
        result.IsA().Destructor(result)
    
        # now perform a search for the CL specified by the input 
        model_normal.setConstant(True)
        step_size = model_normal.getError()
        model_normal.setVal(model_normal.getVal()+step_size)
        number_of_tries = 0
    
        number_of_steps = 0
        while not exit_requested:
            result = model.fitTo(data, \
                                       ROOT.RooFit.Save(True),\
                                       ROOT.RooFit.PrintLevel(-1),\
                                       ROOT.RooFit.Verbose(False),\
                                       ROOT.RooFit.Hesse(False),\
                                       ROOT.RooFit.Minos(False))#,\
        
            # Check fit status
            if result.status() != 0: 
                print "Possible error in status"
                result.IsA().Destructor(result)
                return retry_error 
    
            
            distance_traveled = -result.minNll() - new_minNll
            new_minNll = -result.minNll()
            distance_to_go = orig_Nll - new_minNll - conf_level
            # IMPORTANT (see note above)
            # Manually cleanning up
            result.IsA().Destructor(result)
    
            # Check results
            #print "CL: ", conf_level
            #print "Diff: ", orig_Nll - new_minNll 
            #print "MN: ", model_normal.getVal() 
            #print "Distance to go: ", distance_to_go
            #print "Distance traveled: ", distance_traveled
            #print "Step size: ", step_size 
            diff = orig_Nll - new_minNll - conf_level
            if math.fabs(distance_to_go) < tolerance: 
                # We've reached converegence within tolerance, get out
                break
            step_size *= distance_to_go/distance_traveled 
            model_normal.setVal(model_normal.getVal() + step_size)
            number_of_steps += 1
            # Trying to avoid getting stuck in a loop.
            if number_of_steps > 200: return retry_error
           
        # We're done, return results
        if exit_requested: return None
        return (model_normal.getVal(), \
                model_normal.getVal()*mult_factor,\
                orig_Nll,\
                new_minNll)
     
    def scan_confidence_value_space_for_model(self, model, data_model, \
                                              model_normal, mult_factor,\
                                              variables, number_of_events,\
                                              number_iterations, cl):
    
        list_of_values = []
        #var_argset = ROOT.RooArgSet(energy, time)
        i = 0
        confidence_value = ROOT.TMath.ChisquareQuantile(cl, 1) 
        while i < number_iterations:
            print "Process %s: Iteration (%i) of (%i)" % (os.getpid(), i+1, number_iterations)
            # Generate the data, use Extended flag
            # because the number_of_events is just
            # an expected number.
            model_normal.setVal(0)
            data_set_func = data_model.generate(\
                variables,\
                number_of_events, \
                ROOT.RooFit.Extended(True))
    
            if not data_set_func:
                print "Background entries are much too low, need to estimate with FC or Rolke."
                continue
            # Perform the fit and find the limits
            get_val = self.find_confidence_value_for_model(
                model, \
                data_set_func, \
                model_normal, \
                confidence_value/2,\
                mult_factor) 
    
            if not get_val: 
                # There was an error somewhere downstream
                # or an interrupt was signalled
                # Get out
                break
            elif get_val==(0,0,0,0): continue
    
            # Store the results
            list_of_values.append(get_val)
            i += 1
    
            # ROOT doesn't play nicely with python always, 
            # so we have to delete by hand
            data_set_func.IsA().Destructor(data_set_func)
    
        #var_argset.IsA().Destructor(var_argset)
        return list_of_values

def main( total_time, threshold, energy_max, kilograms, \
          background_rate, wimp_mass, output_file,\
          number_iterations, cl, num_cpus, max_time, \
          constant_time, constant_energy):


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

    # Step 1: Instantiate child processes.  i call them 'threads', but there
    # are actually a forked process.
    thread_list = []
    for i in range(num_cpus):
        r, w = os.pipe()
        thread_list.append(\
            (r,w,CalculateObject( total_time, threshold, energy_max, \
             kilograms, background_rate, wimp_mass, \
             number_iterations, cl, constant_time, \
             constant_energy, w)))

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
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGALRM, exit_handler)
    signal.alarm(max_time)
    print "Parent (%i) waiting for processes." % os.getpid()
    sys.stdout.flush()
    # Parent only
    # Step 3: Gather, sucking on the pipes until close
    # and waiting for all child processes to clean up 
    results_list = [] 
    signal_received = False
    for pid, read_pipe in open_threads:
        while 1:
            try:
                print "Parent (%i) waiting for process: %i" % (os.getpid(), pid)
                sys.stdout.flush()
                a_list = eval(read_pipe.read())
                print "Parent (%i) collected for process: %i" % (os.getpid(), pid)
                sys.stdout.flush()
                break
            except IOError, e:
                print "Parent (%i) received signal" % os.getpid()
                sys.stdout.flush()
                if e.args[0] == errno.EINTR:
                    if not signal_received: 
                        signal_received = True
                        signal.alarm(1)
                    else:
                        for apid, arp in open_threads:
                            # Make sure they got the signal
                            print "Parent (%i) sending signal to pid: %i" % (os.getpid(),apid)
                            sys.stdout.flush()
                            try:
                                os.kill(apid, signal.SIGUSR1)
                            except: pass
                else: 
                    print "Caught IOError: ", e
                    sys.stdout.flush()
                    raise e
                pass
                
        for val in a_list: results_list.append(val)

    signal.alarm(0)
    for i in range(len(open_threads)):
        print os.waitpid(-1, 0)
    print "Gathered %i processes." % num_cpus
    sys.stdout.flush()
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

    output_tree.Branch("total_time", total_time_out, "total_time/D")
    output_tree.Branch("threshold", threshold_out, "threshold/D")
    output_tree.Branch("energy_max", energy_max_out, "energy_max/D")
    output_tree.Branch("mass_of_detector", mass_of_detector_out, "mass_of_detector/D")
    output_tree.Branch("background_rate", background_rate_out, "background_rate/D")
    output_tree.Branch("wimp_mass", wimp_mass_out, "wimp_mass/D")
    output_tree.Branch("model_amplitude", model_amplitude_out, "model_amplitude/D")
    output_tree.Branch("cross_section", cross_section_out, "cross_section/D")
    output_tree.Branch("orig_max_likelihood", likelihood_max_out, "orig_max_likelihood/D")
    output_tree.Branch("final_max_likelihood", final_likelihood_max_out, "final_max_likelihood/D")

    for value,cs,orig_nll,new_nll in results_list:
        model_amplitude_out[0] = value
        cross_section_out[0] = cs
        likelihood_max_out[0] = orig_nll
        final_likelihood_max_out[0] = new_nll
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
                      help="Define the number of processors", default=detectCPUs())
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
    parser.add_option("-i", "--num_iter", dest="num_iter",\
                      help="Define the number of iterations",\
                      default=10)
    parser.add_option("-c", "--confidence_level", dest="confidence_level",\
                      help="Define the CL of the calculation",\
                      default=0.9)
    parser.add_option("-a", "--max_time", dest="max_time",\
                      help="Set the max time [seconds] until this program shuts down",\
                      default=0)
    parser.add_option("--constant_time", action="store_true", dest="constant_time",\
                      help="Integrate over time, do not fit over time",\
                      default=False)
    parser.add_option("--constant_energy", action="store_true", dest="constant_energy",\
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

Process:
    Using cpu number: %i
    Iterations on each cpu: %i
    Output file: %s
    Max time (seconds): %s
    """ % ( threshold, energy_max, \
            kilograms, background_rate,\
            wimp_mass, total_time, str(constant_time),\
            str(constant_energy), cl,\
            num_cpus, num_iter, output_file,\
            max_string )

    # Force flush so we only see this once
    sys.stdout.flush()
    # GO
    main(total_time, threshold, \
         energy_max, kilograms, \
         background_rate, wimp_mass, \
         output_file, num_iter, cl, num_cpus,\
         max_time, constant_time, constant_energy)
