import BaseCalculation
import ROOT

class OscillationSensitivityCalculation(BaseCalculation.BaseCalculation):
    def find_confidence_value_for_model(self, \
                                        model, \
                                        data, \
                                        model_amplitude, \
                                        conf_level, \
                                        mult_factor, \
                                        print_level = -1, \
                                        verbose = False, \
                                        tolerance = 0.001):
    
        # First ML fit, let everything float
        if self.is_exit_requested(): return None
        model_amplitude.setConstant(False)
        model_amplitude.setVal(1)
        result = model.fitTo(data,\
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
    
        minimized_value = model_amplitude.getVal()
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
    
        model_amplitude.setConstant(True)
        model_amplitude.setVal(0)
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
    
        new_minNll = -result.minNll()
        # Manually cleanning up
        result.IsA().Destructor(result)
    
        # We're done, return results
        return { 'best_fit_model' : minimized_value, \
                 'orig_min_negloglikelihood' : orig_Nll, \
                 'final_min_negloglikelihood' : new_minNll } 
 

