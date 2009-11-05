try:
    import ROOT 
    from wimp_model import AllWIMPModels
    import os
    import signal
    import math
except ImportError:
    print "Error importing"
    raise 


class WIMPModel:
    """
    Class handles performing a sensitivity calculation
    for a Ge detector given the input parameters.
    FixME: This class uses AllWIMPModels class, but doesn't
    allow an interface to change those values.
    """
    def __init__(self, \
                 total_time, \
                 threshold, \
                 energy_max,\
                 kilograms, \
                 background_rate, \
                 wimp_mass, \
                 number_iterations, \
                 cl,\
                 constant_time, \
                 constant_energy, \
                 output_pipe, \
                 exit_manager):

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
        self.is_initialized = False
        self.exit_manager = exit_manager 
        self.retry_error = (0,0,0,0)

    # overload this function for derived classes.
    def initialize(self):

        if self.is_initialized: return
        self.wimpClass = AllWIMPModels(time_beginning=0, \
            time_in_years=self.total_time, \
            energy_threshold=self.threshold, \
            energy_max=self.energy_max,\
            mass_of_wimp=self.wimp_mass)
 
        self.variables = ROOT.RooArgSet()
        if self.constant_time:
            self.wimpClass.get_time().setVal(0)
            self.wimpClass.get_time().setConstant(True)
        else:
            self.variables.add(self.wimpClass.get_time())
        if not self.constant_energy:
            self.variables.add(self.wimpClass.get_energy())

        # This is where we define our models
        self.background_model =  self.wimpClass.get_flat_model()
        self.model = self.wimpClass.get_WIMP_model(self.wimp_mass)
        self.norm = self.wimpClass.get_normalization().getVal()
        self.is_initialized = True


    def run(self):
        """
        Do the work.  Perform the fits, and return the results
        """
        ROOT.gROOT.SetBatch()

        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGUSR1, self.exit_manager.exit_handler)

        ROOT.RooRandom.randomGenerator().SetSeed(0)
        ROOT.RooMsgService.instance().setSilentMode(True)
        ROOT.RooMsgService.instance().setGlobalKillBelow(3)
        self.initialize()

        # Open the pipe to write back on
        write_pipe = os.fdopen(self.output_pipe, 'w') 

        total_counts = int(self.kilograms*self.background_rate*\
            (self.energy_max-self.threshold)*\
            self.total_time*365)

        # Set the numeric integration properties, this is important
        # since some of these integrals are difficult to do
        precision = ROOT.RooNumIntConfig.defaultConfig()
        precision.setEpsRel(1e-8)
        precision.setEpsAbs(1e-8)
        precision.method2D().setLabel("RooIntegrator2D")

        # Now perform the integral
        norm_integral_val = self.model.createIntegral(self.variables).getVal()
        # This integral is in units of pb^{-1} kg^{-1} yr d^{-1}
        if norm_integral_val == 0.0:
            print "Integral defined as 0, meaning it is below numerical precision"
            print "Aborting further calculation"
            write_pipe.write(str([]))
            write_pipe.close()
            return
 
        background_normal = ROOT.RooRealVar("flat_normal", "flat_normal", \
                                      total_counts, 0, 3*total_counts)
        model_normal = ROOT.RooRealVar("model_normal", "model_normal", \
                                      1, 0, 100000)
        model_extend = ROOT.RooExtendPdf("model_extend", "model_extend", \
                                          self.model, model_normal)
        background_extend = ROOT.RooExtendPdf("background_extend", "background_extend", \
                                          self.background_model, background_normal)
        added_pdf = ROOT.RooAddPdf("b+s", "Background + Signal", \
                                   ROOT.RooArgList(background_extend, model_extend))
        
        # Set up signal handler

        results_list = self.scan_confidence_value_space_for_model(added_pdf, 
                                              self.background_model, model_normal, \
                                              self.norm, self.variables, total_counts, \
                                              self.number_iterations, self.cl)

        write_pipe.write(str(results_list))
        write_pipe.close()


    def find_confidence_value_for_model(self, \
                                        model, \
                                        data, \
                                        model_normal, \
                                        conf_level, \
                                        mult_factor, \
                                        tolerance = 0.001):
    
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
            return self.retry_error 
    
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
        while not self.exit_manager.is_exit_requested():
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
                return self.retry_error 
    
            
            distance_traveled = -result.minNll() - new_minNll
            new_minNll = -result.minNll()
            distance_to_go = orig_Nll - new_minNll - conf_level
            # IMPORTANT (see note above)
            # Manually cleanning up
            result.IsA().Destructor(result)
    
            # Check results
            diff = orig_Nll - new_minNll - conf_level
            if math.fabs(distance_to_go) < tolerance: 
                # We've reached converegence within tolerance, get out
                break
            step_size *= distance_to_go/distance_traveled 
            model_normal.setVal(model_normal.getVal() + step_size)
            number_of_steps += 1
            # Trying to avoid getting stuck in a loop.
            if number_of_steps > 200: return self.retry_error
           
        # We're done, return results
        if self.exit_manager.is_exit_requested(): return None
        return (model_normal.getVal(), \
                model_normal.getVal()*mult_factor,\
                orig_Nll,\
                new_minNll)
     
    def scan_confidence_value_space_for_model(self, model, data_model, \
                                              model_normal, mult_factor,\
                                              variables, number_of_events,\
                                              number_iterations, cl):
    
        list_of_values = []
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
                break
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
            elif get_val == self.retry_error: continue
    
            # Store the results
            list_of_values.append(get_val)
            i += 1
    
            # ROOT doesn't play nicely with python always, 
            # so we have to delete by hand
            data_set_func.IsA().Destructor(data_set_func)
    
        return list_of_values


def calculate_object_engine(calc_object_name):
    if calc_object_name == "WIMPModel":
        return WIMPModel
    return None
