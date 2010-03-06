import ExclusionCalculation
import ROOT
import os
import math
class DataCalculation(ExclusionCalculation.ExclusionCalculation):

    """
    This class handles calculating the exclusion limits given a 
    certain input data set.  We have to overload 
    scan_confidence_value_space_for_model to do this.
    """
    def find_confidence_value_for_model(self, 
                                        model, 
                                        data, 
                                        model_amplitude, 
                                        conf_level, 
                                        mult_factor, 
                                        print_level = -1, 
                                        verbose = False, 
                                        debug = False,
                                        tolerance = 0.0001):
    
        # First ML fit, let everything float
        # Initial fit, this is to get everything in decent
        # areas around the true values.
        model_amplitude.setConstant(True)
        model_amplitude.setVal(0)
        nll = model.createNLL(data,
                             ROOT.RooFit.Verbose(verbose))
       
        model_amplitude.setVal(model_amplitude.getMax())
        minuit = ROOT.RooMinuit(nll)
        minuit.migrad()

        # Now fit with the model_amplitude
        while 1:
            model_amplitude.setConstant(False)
            minuit.migrad()
            if math.fabs(model_amplitude.getVal() - model_amplitude.getMin()) < 0.01: 
                #model_amplitude.setMin(model_amplitude.getMin() - 100)
                print "model amplitude at lower min, resetting and finding minimum: ", model_amplitude.getMin()
                break
            else: break

        minimized_value =  model_amplitude.getVal()
        step_size = model_amplitude.getError()
        pll_frac = nll.createProfile(ROOT.RooArgSet(model_amplitude)) 
        pll_frac.getVal()
        print model_amplitude.getVal()
        
        if conf_level == 0: return None 
        if debug:
            aframe = model_amplitude.frame(ROOT.RooFit.Bins(40), ROOT.RooFit.Range(minimized_value-40, minimized_value+50))
            nll.plotOn(aframe, ROOT.RooFit.ShiftToZero())
            pll_frac.plotOn(aframe,ROOT.RooFit.LineColor(5))
            aframe.SetMaximum(2)
            aframe.SetMinimum(-0.5)
            aframe.Draw()
            self.c1.Update()
            raw_input("Hit Enter to continue")
 
        orig_Nll = 0  
        new_minNll = orig_Nll 
    
        print "Minimized value: ", minimized_value
        print "Step size: ", step_size
        #model_amplitude.setVal(0)
        #if math.fabs(model_amplitude.getVal() - model_amplitude.getMin()) < 0.01: step_size = 1
        model_amplitude.setVal(minimized_value+step_size)
        number_of_tries = 0
    
        number_of_steps = 0
        new_step = 1
        original_step_size = step_size
        while not self.is_exit_requested():
            #print model_amplitude.getVal()
            temp = pll_frac.getVal() 
            if temp < 0:
                # This is a problem, some discontinuity in the LL space?
                print "PLL negative, discontinuity: " 
                pll_frac.Print('v')
                nll.Print('v')
                raise "PLLDiscontinuityFitException"
            #print model_amplitude.getVal()
            print 
            # Check fit status
                      
            distance_traveled = temp - new_minNll
            new_minNll = temp 
            distance_to_go = conf_level - new_minNll
    
            # Check results
            if math.fabs(distance_to_go) < tolerance: 
                # We've reached converegence within tolerance, get out
                break
            if distance_traveled == 0: distance_traveled = distance_to_go 
            step_size *= distance_to_go/distance_traveled 
            print temp, step_size, distance_traveled, distance_to_go, model_amplitude.getVal()
            model_amplitude.setVal(model_amplitude.getVal() + step_size)
            if model_amplitude.getVal() == model_amplitude.getMax():
                model_amplitude.setMax(model_amplitude.getVal()*2)
            number_of_steps += 1
            # Trying to avoid getting stuck in a loop.
            if number_of_steps > 20: tolerance *= 2 
           
        # We're done, return results
        if self.is_exit_requested(): return None
        print model_amplitude.getVal()
        print mult_factor
        print model_amplitude.getVal()*mult_factor
        return {'model_amplitude' : model_amplitude.getVal(), 
                'cross_section' : model_amplitude.getVal()*mult_factor,
                'orig_min_negloglikelihood' : orig_Nll,
                'final_min_negloglikelihood' : new_minNll}
 
    def scan_confidence_value_space_for_model(self, 
                                              model, 
                                              data_model, 
                                              model_amplitude, 
                                              mult_factor,
                                              variables, 
                                              number_of_events,
                                              number_iterations, 
                                              cl,
                                              show_plots = False,
                                              debug_output = False):
    
        print_level = -1
        verbose = debug_output
        if debug_output: print_level = 3

        list_of_values = []
        i = 0
        confidence_value = ROOT.TMath.ChisquareQuantile(cl, 1) 
        if debug_output:
            print "Process %s: Fitting to data." \
                % (os.getpid())
        # Generate the data, use Extended flag
        # because the number_of_events is just
        # an expected number.
        model_amplitude.setVal(0)
        data_set_func = data_model
        get_val = self.find_confidence_value_for_model(
            model, 
            data_set_func, 
            model_amplitude, 
            0/2,
            mult_factor,
            print_level,
            verbose,
            show_plots) 

        if show_plots:
            var_iter = variables.createIterator()
            while 1:
                var_obj = var_iter.Next()
                if not var_obj: break
                aframe = var_obj.frame()
                ROOT.RooAbsData.plotOn(data_set_func, aframe)
                model.plotOn(aframe)
                model.plotOn(aframe, ROOT.RooFit.Components("WIMPPDF_With_Time_And_Escape_Vel"), ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                model.plotOn(aframe, ROOT.RooFit.Components("simple model"), ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                aframe.Draw()
                self.c1.Update()
                raw_input("Hit Enter to continue")
          

        # Perform the fit and find the limits
        get_val = None
        while 1:
            get_val = self.find_confidence_value_for_model(
                model, 
                data_set_func, 
                model_amplitude, 
                confidence_value/2,
                mult_factor,
                print_level,
                verbose,
                show_plots) 
            
            if not get_val: 
                # There was an error somewhere downstream
                # or an interrupt was signalled
                # Get out
                break
            elif get_val == self.retry_error: 
                # Calling function requested a retry
                continue
            else: break
    
            # Store the results
        list_of_values.append(get_val)
    
        if show_plots:
            var_iter = variables.createIterator()
            while 1:
                var_obj = var_iter.Next()
                if not var_obj: break
                aframe = var_obj.frame()
                ROOT.RooAbsData.plotOn(data_set_func, aframe)
                model.plotOn(aframe)
                model.plotOn(aframe, ROOT.RooFit.Components("WIMPPDF_With_Time_And_Escape_Vel"), ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                model.plotOn(aframe, ROOT.RooFit.Components("simple model"), ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                aframe.Draw()
                self.c1.Update()
                raw_input("Hit Enter to continue")
                
        return list_of_values

