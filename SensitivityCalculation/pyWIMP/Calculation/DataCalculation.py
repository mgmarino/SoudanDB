import ExclusionCalculation
import ROOT
import os
import math
from exceptions import Exception
from ..utilities.utilities import rescale_frame
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
    
        pars = model.getParameters(data)
        expo_const = pars.find("expo_const_")
        if expo_const:
            expo_const.setConstant(False)
        # First ML fit, let everything float
        # Initial fit, this is to get everything in decent
        # areas around the true values.
        model_amplitude.setConstant(True)
        model_amplitude.setVal(0)
        nll = model.createNLL(data,
                             ROOT.RooFit.Verbose(verbose))
       
        #model_amplitude.setVal(model_amplitude.getMin())
        minuit = ROOT.RooMinuit(nll)
        minuit.migrad()

        # OK, this is a hack, make the non-amplitude parameters constant
        if expo_const:
            expo_const.setConstant(True)

        # Now fit with the model_amplitude
        model_amplitude.setConstant(False)
        minuit.migrad()
        initial_saved_result = model.fitTo(data, ROOT.RooFit.Verbose(verbose), 
                                   ROOT.RooFit.PrintLevel(print_level),
                                   ROOT.RooFit.Save(True))
        #while 1:
        #    model_amplitude.setConstant(False)
        #    minuit.migrad()
        #    if math.fabs(model_amplitude.getVal() - model_amplitude.getMin()) < 0.01: 
                #model_amplitude.setMin(model_amplitude.getMin() - 100)
        #        print "model amplitude at lower min, resetting and finding minimum: ", model_amplitude.getMin()
        #        break
        #    else: break

        minimized_value =  model_amplitude.getVal()
        step_size = model_amplitude.getError()

        pll_frac = nll.createProfile(ROOT.RooArgSet(model_amplitude)) 
        pll_frac.getVal()
        
        if conf_level == 0: return None 
        min_value = minimized_value - 100 
        if min_value < 0: min_value = 0
        
        max_range = minimized_value + 100

        model_amplitude.setVal(max_range)
        while pll_frac.getVal() < conf_level: 
            max_range += 100
            model_amplitude.setVal(max_range)
            if model_amplitude.getVal() == model_amplitude.getMax():
                self.logging("Resetting maximum:", model_amplitude.getMax() )
                model_amplitude.setMax(model_amplitude.getVal()*2)

        if expo_const:
            expo_const.setConstant(False)
        # First ML fit, let everything float
        # Initial fit, this is to get everything in decent
        # areas around the true values.
        model_amplitude.setConstant(True)
        model_amplitude.setVal(0)
        nll = model.createNLL(data,
                             ROOT.RooFit.Verbose(verbose))
       
        #model_amplitude.setVal(model_amplitude.getMin())
        minuit = ROOT.RooMinuit(nll)
        minuit.migrad()

        # OK, this is a hack, make the non-amplitude parameters constant
        if expo_const:
            expo_const.setConstant(True)

        # Now fit with the model_amplitude
        model_amplitude.setConstant(False)
        minuit.migrad()

        aframe = model_amplitude.frame(ROOT.RooFit.Bins(100), 
                   ROOT.RooFit.Range(min_value, max_range))
        nll.plotOn(aframe, ROOT.RooFit.ShiftToZero(), ROOT.RooFit.Name("nll_plot"))
        pll_frac.plotOn(aframe,ROOT.RooFit.LineColor(5), ROOT.RooFit.Name("pll_frac_plot"))
        aframe.SetMaximum(2)
        aframe.SetMinimum(-0.5)
        aframe.SetTitle("%s (LL, Profile LL)" % self.plot_base_name)
        pll_curve = aframe.getCurve("pll_frac_plot")
        nll_curve = aframe.getCurve("nll_plot")

        if debug:
            aframe.Draw()
            self.c1.Update()
            if self.print_out_plots:
                # HAck!
                title = aframe.GetTitle()
                title = title.replace(' ','').replace('(','').replace(')','').replace(',','') 
                self.c1.Print(title + ".eps")
            else:
                raw_input("Hit Enter to continue")
 
        # Now we search more finely for the correct value
        step_size = 0.05
        while pll_curve.Eval(model_amplitude.getVal()) < conf_level: 
            model_amplitude.setVal(model_amplitude.getVal() + step_size)

        model_amplitude.setConstant(True)
        final_saved_result = model.fitTo(data, ROOT.RooFit.Verbose(verbose), 
                                   ROOT.RooFit.PrintLevel(print_level),
                                   ROOT.RooFit.Save(True))
        #orig_Nll = 0  
        #new_minNll = orig_Nll 
        #if (math.fabs(minimized_value - model_amplitude.getMin())) < 0.2: step_size = 10
        #model_amplitude.setVal(minimized_value+step_size)
        
        #self.logging( "Minimized value: ", minimized_value )
        #self.logging( "Step size: ", step_size )
        #number_of_tries = 0
        
        #number_of_steps = 0
        #new_step = 1
        #original_step_size = step_size
        #while not self.is_exit_requested():
        #    #print model_amplitude.getVal()
        #    temp = pll_frac.getVal() 
        #    if temp < 0:
        #        # This is a problem, some discontinuity in the LL space?
        #        self.logging( "PLL negative, discontinuity: " )
        #        pll_frac.Print('v')
        #        nll.Print('v')
        #        raise Exception("PLLDiscontinuityFitException")
        #    # Check fit status
        #              
        #    distance_traveled = temp - new_minNll
        #    new_minNll = temp 
        #    distance_to_go = conf_level - new_minNll
        #
        #    # Check results
        #    if math.fabs(distance_to_go) < tolerance: 
        #        # We've reached converegence within tolerance, get out
        #        break
        #    if distance_traveled == 0: distance_traveled = distance_to_go 
        #    step_size *= distance_to_go/distance_traveled 
        #    self.logging( temp, step_size, distance_traveled, distance_to_go, model_amplitude.getVal() )
        #    model_amplitude.setVal(model_amplitude.getVal() + step_size)
        #    if model_amplitude.getVal() == model_amplitude.getMax():
        #        self.logging("Resetting maximum:", model_amplitude.getMax() )
        #        model_amplitude.setMax(model_amplitude.getVal()*2)
        #    number_of_steps += 1
        #    # Trying to avoid getting stuck in a loop.
        #    if number_of_steps > 50: 
        #        tolerance *= 2 
        #        self.logging("Resetting tolerance: ", tolerance)
        #        number_of_steps = 0

        #   
        ## We're done, return results
        if self.is_exit_requested(): return None
        return {'pll_curve' : pll_curve,
                'nll_curve' : nll_curve,
                'mult_factor' : mult_factor,
                'final_fit_result' : final_saved_result,
                'initial_fit_result' : initial_saved_result,
                'model_amplitude' : model_amplitude.getVal(), 
                'cross_section' : model_amplitude.getVal()*mult_factor}
        #return {'model_amplitude' : model_amplitude.getVal(), 
        #        'cross_section' : model_amplitude.getVal()*mult_factor,
        #        'orig_min_negloglikelihood' : orig_Nll,
        #        'final_min_negloglikelihood' : new_minNll}
 
    def scan_confidence_value_space_for_model(self, 
                                              model, 
                                              data_model, 
                                              model_amplitude, 
                                              mult_factor,
                                              variables, 
                                              number_of_events,
                                              number_iterations, 
                                              cl):
    
        print_level = -1
        verbose = self.debug
        if self.debug: print_level = 3
        show_plots = self.show_plots or self.print_out_plots

        list_of_values = []
        i = 0
        confidence_value = ROOT.TMath.ChisquareQuantile(cl, 1) 
        if self.debug:
            self.logging( "Process %s: Fitting to data." )
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
            var_iter = model.getObservables(data_set_func).createIterator()
            while 1:
                var_obj = var_iter.Next()
                if not var_obj: break
                aframe = var_obj.frame()
                ROOT.RooAbsData.plotOn(data_set_func, aframe)
                model.plotOn(aframe)
                model.plotOn(aframe, 
                             ROOT.RooFit.Components("WIMPPDF_With_Time_And_Escape_Vel"), 
                             ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                model.plotOn(aframe, 
                             ROOT.RooFit.Components("simple model"), 
                             ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                aframe.SetTitle("%s (Initial fit)" % self.plot_base_name)
                bin_width = aframe.getFitRangeBinW()
                axis = rescale_frame(self.c1, aframe, 1./bin_width, "Counts/keV")
                axis.CenterTitle()
                aframe.Draw()
                self.c1.Update()
                if self.print_out_plots:
                    title = aframe.GetTitle()
                    title = title.replace(' ','').replace('(','').replace(')','').replace(',','') 
                    self.c1.Print(title + ("%s.eps" % var_obj.GetName()))
                else:
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
            var_iter = model.getObservables(data_set_func).createIterator()
            while 1:
                var_obj = var_iter.Next()
                if not var_obj: break
                aframe = var_obj.frame()
                ROOT.RooAbsData.plotOn(data_set_func, aframe)
                model.plotOn(aframe)
                model.plotOn(aframe, 
                             ROOT.RooFit.Components("WIMPPDF_With_Time_And_Escape_Vel"), 
                             ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                model.plotOn(aframe, ROOT.RooFit.Components("simple model"), 
                             ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
                aframe.SetTitle("%s (Final fit)" % self.plot_base_name)
                aframe.Draw()
                self.c1.Update()
                if self.print_out_plots:
                    title = aframe.GetTitle()
                    title = title.replace(' ','').replace('(','').replace(')','').replace(',','') 
                    self.c1.Print(title + ("%s.eps" % var_obj.GetName()))
                else:
                    raw_input("Hit Enter to continue")
                
        return list_of_values

