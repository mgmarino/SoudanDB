import ExclusionCalculation
import ROOT
import os
import math
from exceptions import Exception
from ..utilities.utilities import rescale_frame
import numpy
class DataCalculation(ExclusionCalculation.ExclusionCalculation):

    """
    This class handles calculating the exclusion limits given a 
    certain input data set.  We have to overload 
    scan_confidence_value_space_for_model to do this.
    """

    def print_plot(self, model, data, title = "", scaling = 1.):
        var_iter = model.getObservables(data).createIterator()
        while 1:
            var_obj = var_iter.Next()
            if not var_obj: break
            aframe = var_obj.frame()
            ROOT.RooAbsData.plotOn(data, aframe)
            model.plotOn(aframe)
            model.plotOn(aframe, 
                 ROOT.RooFit.Components("WIMPPDF_With_Time_And_Escape_Vel"), 
                 ROOT.RooFit.LineStyle(ROOT.RooFit.kDashed))
            model.plotOn(aframe, 
                 ROOT.RooFit.Components("energy_pdf_*"), 
                 ROOT.RooFit.LineWidth(4),
                 ROOT.RooFit.LineStyle(ROOT.RooFit.kDotted),
                 ROOT.RooFit.LineColor(ROOT.RooFit.kRed))
            model.plotOn(aframe, 
                 ROOT.RooFit.Components("gamma*"), 
                 ROOT.RooFit.LineWidth(4),
                 ROOT.RooFit.LineColor(ROOT.RooFit.kRed))
            aframe.SetTitle("%s %s" % 
                            (self.plot_base_name, title))
            #bin_width = aframe.getFitRangeBinW()
            #axis = rescale_frame(self.c1, aframe, scaling/bin_width, axis_title)
            #axis.CenterTitle()
            aframe.Draw()
            self.c1.Update()
            if self.print_out_plots:
                title = aframe.GetTitle()
                title = title.replace(' ','').replace('(','').replace(')','').replace(',','') 
                self.c1.Print(title + ("%s.eps" % var_obj.GetName()))
            else:
                raw_input("Hit Enter to continue")


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
    
        absolute_min = -100
        pars = model.getParameters(data)
        #expo_const = pars.find("expo_const_one")
        expo_coef = pars.find("expo_const_one")
        #if expo_const:
        #    expo_const.setConstant(False)
        # First ML fit, let everything float
        # Initial fit, this is to get everything in decent
        # areas around the true values.
        model_amplitude.setError(0.5)
        model_amplitude.setVal(0)
        model_amplitude.setMin(-10)
        model_amplitude.setConstant(True)
        nll = model.createNLL(data,
                              ROOT.RooFit.Verbose(verbose))
       
        #model_amplitude.setVal(model_amplitude.getMin())
        minuit = ROOT.RooMinuit(nll)
        minuit.migrad()

        # OK, this is a hack, make the non-amplitude parameters constant
        #if expo_coef:
        #    expo_coef.setConstant(True)

        # Now fit with the model_amplitude
        model_amplitude.setVal(0)
        model_amplitude.setConstant(False)
        minuit.migrad()
        distance_from_min = 20.
        while math.fabs(model_amplitude.getMin() - model_amplitude.getVal()) < distance_from_min: 
           model_amplitude.setMin(model_amplitude.getMin() - distance_from_min) 
           if model_amplitude.getMin() < absolute_min: break
           minuit.migrad()

        print model_amplitude.getMin(), model_amplitude.getVal()
        initial_saved_result = minuit.save() 

        minimized_value =  model_amplitude.getVal()
        step_size = model_amplitude.getError()

        pll_frac = nll.createProfile(ROOT.RooArgSet(model_amplitude)) 
        pll_frac.getVal()
        
        if conf_level == 0: return None 
        min_value = minimized_value - 100 
        if min_value < model_amplitude.getMin(): 
            min_value = model_amplitude.getMin()
        
        max_range = minimized_value + 100

        model_amplitude.setVal(max_range)
        while pll_frac.getVal() < 2*conf_level: 
            max_range += 100
            model_amplitude.setVal(max_range)
            if model_amplitude.getVal() == model_amplitude.getMax():
                self.logging("Resetting maximum:", model_amplitude.getMax() )
                model_amplitude.setMax(model_amplitude.getVal()*2)

        #if expo_const:
        #    expo_const.setConstant(False)
        # First ML fit, let everything float
        # Initial fit, this is to get everything in decent
        # areas around the true values.
        nll = model.createNLL(data,
                             ROOT.RooFit.Verbose(verbose))
       
        #model_amplitude.setVal(model_amplitude.getMin())
        minuit = ROOT.RooMinuit(nll)
        #minuit.setPrintLevel(print_level)
        #minuit.migrad()

        # OK, this is a hack, make the non-amplitude parameters constant
        #if expo_const:
        #    expo_const.setConstant(True)

        # Now fit with the model_amplitude
        model_amplitude.setVal(0)
        model_amplitude.setConstant(False)
        minuit.migrad()
        first_res = minuit.save()
        first_res.Print('v')
        model_amplitude.setConstant(True)
        output_list = []
        pll_curve = ROOT.RooCurve()
        pll_curve.SetName("pll_frac_plot") 
        orig = first_res.minNll() 
        output_dict = {}
        
        #aplot = minuit.contour(model_amplitude, expo_coef, 1, 2, 3)
        #output_dict["contour"] = aplot
        #return output_dict
        for i in numpy.arange(min_value, max_range + 1., (max_range - min_value)/100.):
            print "Perfoming: ", i 
            model_amplitude.setVal(i)
            j = 0
            while 1:
                minuit.migrad()
                res = minuit.save(str(i)) 
                expo_coef.setConstant(False) 
                if j == 1: break
                if math.fabs(res.correlation('exp_coef_', 'expo_const_one')) > 0.98:
                    expo_coef.setConstant(True) 
                    print "Set constant."
                else: break
                j += 1
                
            #if debug:
            #    self.print_plot(model, data, str(i))
            print "Status, ", res.status()
            output_list.append((i, res))
            if res.minNll() < orig:  orig = res.minNll()
            output_dict[str(i)] = res 
            
        output_dict['first_fit'] = first_res
        first_res.Print('v')

        for i, res in output_list:
            model_amplitude.setVal(i)
            print i, res.minNll() - orig, res.minNll()
            pll_curve.addPoint(i, res.minNll() - orig)
       

        output_dict['pll_curve'] = pll_curve
        return output_dict
        aframe = model_amplitude.frame(ROOT.RooFit.Bins(100), 
                   ROOT.RooFit.Range(min_value, max_range))
        #nll.plotOn(aframe, ROOT.RooFit.ShiftToZero(), ROOT.RooFit.Name("nll_plot"))
        #pll_frac.plotOn(aframe,ROOT.RooFit.LineColor(5), ROOT.RooFit.Name("pll_frac_plot"))

        aframe.SetMaximum(2)
        aframe.SetMinimum(-2.5)
        aframe.SetTitle("%s (LL, Profile LL)" % self.plot_base_name)

        #pll_curve = aframe.getCurve("pll_frac_plot")
        #nll_curve = aframe.getCurve("nll_plot")
        nll_curve = "nll"

        if debug:
            
            for frame in [ aframe]:
                frame.Draw()
                pll_curve.Draw("L")
                self.c1.Update()
                if self.print_out_plots:
                    # HAck!
                    title = frame.GetTitle()
                    title = title.replace(' ','').replace('(','').replace(')','').replace(',','') 
                    self.c1.Print(title + ".eps")
                else:
                    raw_input("Hit Enter to continue")
 
        return output_dict
        # Now we search more finely for the correct value
        step_size = 0.05
        while pll_curve.Eval(model_amplitude.getVal()) < conf_level: 
            model_amplitude.setVal(model_amplitude.getVal() + step_size)

        model_amplitude.setConstant(True)
        final_saved_result = model.fitTo(data, ROOT.RooFit.Verbose(verbose), 
                                   ROOT.RooFit.SumW2Error(True),
                                   ROOT.RooFit.PrintLevel(print_level),
                                   ROOT.RooFit.Save(True))

        ## We're done, return results
        if self.is_exit_requested(): return None
        return {'pll_curve' : pll_curve,
                'nll_curve' : nll_curve,
                'mult_factor' : mult_factor,
                'final_fit_result' : final_saved_result,
                'initial_fit_result' : initial_saved_result,
                'model_amplitude' : model_amplitude.getVal(), 
                'cross_section' : model_amplitude.getVal()*mult_factor}
 
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

        # Looking for whether or not we have info 
        scaling = 1.
        axis_title = "Counts/keV"
        if "mass_of_detector" in self.input_variables.keys()\
           and "total_time" in self.input_variables.keys():
            kilos = self.input_variables["mass_of_detector"]
            time_in_years = self.input_variables["total_time"]
            scaling = 1./(kilos*time_in_years*365.25)
            axis_title = "Counts/keV/kg/d"
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
                     ROOT.RooFit.Components("energy_pdf_*"), 
                     ROOT.RooFit.LineWidth(4),
                     ROOT.RooFit.LineStyle(ROOT.RooFit.kDotted),
                     ROOT.RooFit.LineColor(ROOT.RooFit.kRed))
                model.plotOn(aframe, 
                     ROOT.RooFit.Components("gamma*"), 
                     ROOT.RooFit.LineWidth(4),
                     ROOT.RooFit.LineColor(ROOT.RooFit.kRed))
                aframe.SetTitle("%s (Initial fit)" % self.plot_base_name)
                bin_width = aframe.getFitRangeBinW()
                axis = rescale_frame(self.c1, aframe, scaling/bin_width, axis_title)
                axis.CenterTitle()
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
                model.plotOn(aframe, 
                     ROOT.RooFit.Components("energy_pdf_*"), 
                     ROOT.RooFit.LineWidth(4),
                     ROOT.RooFit.LineStyle(ROOT.RooFit.kDotted),
                     ROOT.RooFit.LineColor(ROOT.RooFit.kRed))
                model.plotOn(aframe, 
                     ROOT.RooFit.Components("gamma*"), 
                     ROOT.RooFit.LineWidth(4),
                     ROOT.RooFit.LineColor(ROOT.RooFit.kRed))
                aframe.SetTitle("%s (Final fit, %g CL, #sigma: %g pb)" % 
                                (self.plot_base_name, cl, 
                                 mult_factor*model_amplitude.getVal()))
                bin_width = aframe.getFitRangeBinW()
                axis = rescale_frame(self.c1, aframe, scaling/bin_width, axis_title)
                axis.CenterTitle()
                self.c1.Update()
                if self.print_out_plots:
                    title = aframe.GetTitle()
                    title = title.replace(' ','').replace('(','').replace(')','').replace(',','') 
                    self.c1.Print(title + ("%s.eps" % var_obj.GetName()))
                else:
                    raw_input("Hit Enter to continue")
                
        return list_of_values

