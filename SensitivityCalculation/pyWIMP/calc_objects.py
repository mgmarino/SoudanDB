#
# calc_object exports classes which can be 
# used for calculation of sensitivities
#

import ROOT
class WIMPModel:
    """
    Class handles performing a sensitivity calculation
    for a Ge detector given the input parameters.
    FixME: This class uses AllWIMPModels class, but doesn't
    allow an interface to change those values.
    """
    def get_requested_values(cls):
        """
        Returns requested values plus defaults
        """
        return {'total_time' : ('Total time (year)', 5),\
                'threshold' : ('Threshold (keV)', 1),\
                'energy_max' : ('Maximum energy (keV)', 50),\
                'mass_of_detector' : ('Mass of detector (kg)', 1),\
                'background_rate' : ('Background rate (counts/keV/kg/day)', 0.1),\
                'wimp_mass' : ('WIMP mass (GeV/c^-2)', 10),\
                'confidence_level' : ('Confidence level (0 -> 1)', 0.9),\
                'variable_quenching' : ('Set to use variable quenching', False),\
                'constant_time' : ('Set time as constant', False),\
                'constant_energy' : ('Set energy as constant', False) }
    get_requested_values = classmethod(get_requested_values)

    def __init__(self, \
                 output_pipe,\
                 exit_manager,\
                 num_iterations,\
                 input_variables):

        for akey, val in self.get_requested_values().items():
            aval = val[1]
            if akey in input_variables.keys():
                aval = input_variables[akey]
            setattr(self,akey, aval) 
        self.number_iterations = num_iterations
        self.output_pipe = output_pipe
        self.exit_now = False
        self.is_initialized = False
        self.exit_manager = exit_manager 
        self.retry_error = {'again' : True} 
        self.total_counts = int(self.mass_of_detector*\
                                self.background_rate*\
                                (self.energy_max-self.threshold)*\
                                self.total_time*365)

    # overload this function for derived classes.
    def initialize(self):

        if self.is_initialized: return
        from pyWIMP.DMModels.wimp_model import AllWIMPModels
        self.wimpClass = AllWIMPModels(time_beginning=0, \
            time_in_years=self.total_time, \
            energy_threshold=self.threshold, \
            energy_max=self.energy_max,\
            mass_of_wimp=self.wimp_mass,
            constant_quenching=(not self.variable_quenching))
 
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
        self.model = self.wimpClass.get_WIMP_model_with_escape_vel(self.wimp_mass)
        self.norm = self.wimpClass.get_normalization().getVal()
        self.is_initialized = True

        self.background_normal = ROOT.RooRealVar("flat_normal", \
                                                 "flat_normal", \
                                                 self.total_counts, \
                                                 0,\
                                                 3*self.total_counts)
        self.model_normal = ROOT.RooRealVar("model_normal", \
                                            "model_normal", \
                                            1, 0, 100000)
        self.model_extend = ROOT.RooExtendPdf("model_extend", \
                                              "model_extend", \
                                              self.model, \
                                              self.model_normal)
        self.background_extend = ROOT.RooExtendPdf("background_extend", \
                                                   "background_extend", \
                                                   self.background_model, \
                                                   self.background_normal)
        self.added_pdf = ROOT.RooAddPdf("b+s", \
                                        "Background + Signal", \
                                        ROOT.RooArgList(\
                                        self.background_extend, \
                                        self.model_extend))
 
        self.test_variable = self.model_normal
        self.data_set_model = self.background_model
        self.fitting_model = self.added_pdf
    
    def run(self):
        """
        Do the work.  Perform the fits, and return the results
        """
        import pickle
        import signal
        import os
        ROOT.gROOT.SetBatch()

        ROOT.RooRandom.randomGenerator().SetSeed(0)
        ROOT.RooMsgService.instance().setSilentMode(True)
        ROOT.RooMsgService.instance().setGlobalKillBelow(3)
        self.initialize()

        # Open the pipe to write back on
        write_pipe = os.fdopen(self.output_pipe, 'w') 

        # Set the numeric integration properties, this is important
        # since some of these integrals are difficult to do
        precision = ROOT.RooNumIntConfig.defaultConfig()
        precision.setEpsRel(1e-8)
        precision.setEpsAbs(1e-8)
        precision.method2D().setLabel("RooIntegrator2D")

        # Perform the integral.  This is a bit of sanity check, it this fails, 
        # then we have a problem 
        norm_integral = self.model.createIntegral(self.variables)

        # FixME, this integral sometimes doesn't converge, set a timeout?
        # This integral is in units of pb^{-1} 
        norm_integral_val = norm_integral.getVal()

        if norm_integral_val == 0.0:
            print "Integral defined as 0, meaning it is below numerical precision"
            print "Aborting further calculation"
            write_pipe.write(pickle.dumps({}))
            write_pipe.close()
            return
 
        # Set up signal handler
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGUSR1, self.exit_manager.exit_handler)

       

        results_list = self.scan_confidence_value_space_for_model(self.fitting_model, 
                                              self.data_set_model, self.test_variable, \
                                              self.norm, self.variables, self.total_counts, \
                                              self.number_iterations, self.confidence_level)

        write_pipe.write(pickle.dumps(results_list))
        write_pipe.close()


    def find_confidence_value_for_model(self, \
                                        model, \
                                        data, \
                                        model_normal, \
                                        conf_level, \
                                        mult_factor, \
                                        tolerance = 0.001):
    
        # Error check
        import math
        if conf_level < 0:
            print "Error, CL must be greater than 0"
            return None
    
        # First ML fit, let everything float
        model_normal.setConstant(False)
        model_normal.setVal(1)
        result = model.fitTo(data, \
                             ROOT.RooFit.Save(True),\
                             ROOT.RooFit.PrintLevel(-1),\
                             ROOT.RooFit.Verbose(False),\
                             ROOT.RooFit.Hesse(False),\
                             ROOT.RooFit.Minos(False))
    
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
        return {'model_amplitude' : model_normal.getVal(), \
                'cross_section' : model_normal.getVal()*mult_factor,\
                'orig_min_negloglikelihood' : orig_Nll,\
                'final_min_negloglikelihood' : new_minNll}
     
    def scan_confidence_value_space_for_model(self, model, data_model, \
                                              model_normal, mult_factor,\
                                              variables, number_of_events,\
                                              number_iterations, cl):
    
        list_of_values = []
        i = 0
        confidence_value = ROOT.TMath.ChisquareQuantile(cl, 1) 
        while i < number_iterations:
            #print "Process %s: Iteration (%i) of (%i)" % (os.getpid(), i+1, number_iterations)
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
            elif get_val == self.retry_error: 
                # Calling function requested a retry
                continue
    
            # Store the results
            list_of_values.append(get_val)
            i += 1
    
            # ROOT doesn't play nicely with python always, 
            # so we have to delete by hand
            data_set_func.IsA().Destructor(data_set_func)
    
        return list_of_values

class OscillationSignalDetection(WIMPModel):
    def get_requested_values(cls):
        adict = WIMPModel.get_requested_values()
        del adict['constant_energy']
        del adict['constant_time']
        adict['model_amplitude'] = ('Initial model amplitude', 0.1)
        return adict
    get_requested_values = classmethod(get_requested_values)

    # overload this function for derived classes.
    def initialize(self):

        if self.is_initialized: return
        from pyWIMP.DMModels.wimp_model import AllWIMPModels
        self.wimpClass = AllWIMPModels(\
            time_beginning=0, \
            time_in_years=self.total_time, \
            energy_threshold=self.threshold, \
            energy_max=self.energy_max,\
            mass_of_wimp=self.wimp_mass)
 
        self.variables = ROOT.RooArgSet()
        self.variables.add(self.wimpClass.get_time())

        # This is where we define our models
        self.background =  self.wimpClass.get_flat_model()
        self.model = self.wimpClass.get_simple_oscillation_model()
        self.norm = 1 
        self.is_initialized = True

        
        if self.model_amplitude > 1: self.model_amplitude = 1
        elif self.model_amplitude < 0: self.model_amplitude = 0
        self.signal_percentage = ROOT.RooRealVar("signal_percentage", \
                                            "signal_percentage", \
                                            self.model_amplitude)
        self.background_model = ROOT.RooAddPdf(\
                                "background",\
                                "Data Model",\
                                self.model,\
                                self.background,\
                                self.signal_percentage)

        self.model_normal = ROOT.RooRealVar("model_normal", \
                                            "model_normal", \
                                            1, 0, self.total_counts)
        self.back_normal = ROOT.RooRealVar("back_normal", \
                                           "back_normal", \
                                            self.total_counts, \
                                            0, 3*self.total_counts)

        self.model_extend = ROOT.RooExtendPdf("model_extend",\
                                              "model_extend",\
                                              self.model,\
                                              self.model_normal)

        self.back_extend = ROOT.RooExtendPdf("back_extend",\
                                             "back_extend",\
                                             self.background,\
                                             self.back_normal)
        self.test_variable = self.model_normal
        self.data_set_model = self.background_model
        self.fitting_model = ROOT.RooAddPdf("s+b", \
                             "Signal + Background",\
                             ROOT.RooArgList(\
                             self.model_extend,\
                             self.back_extend))

    def find_confidence_value_for_model(self, \
                                        model, \
                                        data, \
                                        model_normal, \
                                        conf_level, \
                                        mult_factor, \
                                        tolerance = 0.001):
    
        # First ML fit, let everything float
        if self.exit_manager.is_exit_requested(): return None
        model_normal.setConstant(False)
        model_normal.setVal(1)
        result = model.fitTo(data,\
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
    
        minimized_value = model_normal.getVal()
        orig_Nll = -result.minNll()
    
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
    
        model_normal.setConstant(True)
        model_normal.setVal(0)
        result = model.fitTo(data, \
                             ROOT.RooFit.Save(True),\
                             ROOT.RooFit.PrintLevel(-1),\
                             ROOT.RooFit.Verbose(False),\
                             ROOT.RooFit.Hesse(False),\
                             ROOT.RooFit.Minos(False))
        
        # Check fit status
        if result.status() != 0: 
            print "Possible error in status"
            result.IsA().Destructor(result)
            return self.retry_error 
    
        new_minNll = -result.minNll()
        # Manually cleanning up
        result.IsA().Destructor(result)
    
        # We're done, return results
        return { 'best_fit_model' : minimized_value, \
                 'orig_min_negloglikelihood' : orig_Nll, \
                 'final_min_negloglikelihood' : new_minNll } 
 

