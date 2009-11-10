import BaseCalculation
import ROOT
import math

class SensitivityCalculation(BaseCalculation.BaseCalculation):
    def find_confidence_value_for_model(self, \
                                        model, \
                                        data, \
                                        model_amplitude, \
                                        conf_level, \
                                        mult_factor, \
                                        print_level = -1, \
                                        verbose = False, \
                                        tolerance = 0.001):
    
        # Error check
        if conf_level < 0:
            print "Error, CL must be greater than 0"
            return None
    
        # First ML fit, let everything float
        model_amplitude.setConstant(False)
        model_amplitude.setVal(1)
        result = model.fitTo(data, \
                             ROOT.RooFit.Save(True),\
                             ROOT.RooFit.PrintLevel(print_level),\
                             ROOT.RooFit.Verbose(verbose),\
                             ROOT.RooFit.Hesse(False),\
                             ROOT.RooFit.Minos(False))
    
        # Check fit status
        if result.status() != 0: 
            print "Possible error in status"
            result.IsA().Destructor(result)
            return self.retry_error 
    
        minimized_value = model_amplitude.getVal()
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
        model_amplitude.setConstant(True)
        step_size = model_amplitude.getError()
        model_amplitude.setVal(model_amplitude.getVal()+step_size)
        number_of_tries = 0
    
        number_of_steps = 0
        while not self.exit_manager.is_exit_requested():
            result = model.fitTo(data, \
                                 ROOT.RooFit.Save(True),\
                                 ROOT.RooFit.PrintLevel(print_level),\
                                 ROOT.RooFit.Verbose(verbose),\
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
            model_amplitude.setVal(model_amplitude.getVal() + step_size)
            number_of_steps += 1
            # Trying to avoid getting stuck in a loop.
            if number_of_steps > 200: return self.retry_error
           
        # We're done, return results
        if self.exit_manager.is_exit_requested(): return None
        return {'model_amplitude' : model_amplitude.getVal(), \
                'cross_section' : model_amplitude.getVal()*mult_factor,\
                'orig_min_negloglikelihood' : orig_Nll,\
                'final_min_negloglikelihood' : new_minNll}
     
