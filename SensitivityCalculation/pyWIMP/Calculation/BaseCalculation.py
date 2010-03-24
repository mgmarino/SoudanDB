import ROOT
import os
import sys
from exceptions import Exception
class BaseCalculation:

    def __init__(self, exit_manager = None):
        self.exit_manager = exit_manager
        self.retry_error = {'again' : True} 
        self.debug = False
        self.show_plots = False
        self.plot_base_name = ""
        self.input_variables = {}

    def is_exit_requested(self):
        if not self.exit_manager: return False
        return self.exit_manager.is_exit_requested()

    def set_canvas(self, canv): self.c1 = canv
    def set_debug(self, set_d = True): self.debug = set_d 
    def set_print_out_plots(self, set_p = True): 
        self.print_out_plots = set_p 
    def set_show_plots(self, set_p = True): 
        self.show_plots = set_p 
    def set_plot_base_name(self, name): 
        self.plot_base_name = name 

    def set_input_variables(self, input):
        self.input_variables = input

    def logging(self, *strings_to_log): 
        header = "PID(%i), Name(%s): " % (os.getpid(), self.plot_base_name) 
        for astr in strings_to_log: header += " %s" % str(astr)
        sys.stdout.write(header)
        sys.stdout.write('\n')
        sys.stdout.flush()

    def find_confidence_value_for_model(self, 
                                        model, 
                                        data, 
                                        model_amplitude, 
                                        conf_level, 
                                        mult_factor, 
                                        print_level = -1, 
                                        verbose = False, 
                                        tolerance = 0.001):
 
        print "Base Class: BaseCalculation being called."
        return None

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

        list_of_values = []
        i = 0
        confidence_value = ROOT.TMath.ChisquareQuantile(cl, 1) 
        while i < number_iterations:
            if self.debug:
                print "Process %s: Iteration (%i) of (%i)" \
                    % (os.getpid(), i+1, number_iterations)
            # Generate the data, use Extended flag
            # because the number_of_events is just
            # an expected number.
            model_amplitude.setVal(0)
            data_set_func = data_model.generate(
                variables,
                number_of_events, 
                ROOT.RooFit.Extended(True))
    
            if not data_set_func:
                print "Background entries are much too low, need to estimate with FC or Rolke."
                break
            # Perform the fit and find the limits
            get_val = self.find_confidence_value_for_model(
                model, 
                data_set_func, 
                model_amplitude, 
                confidence_value/2,
                mult_factor,
                print_level,
                verbose) 
    
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
    
            if self.show_plots:
                var_iter = variables.createIterator()
                while 1:
                    var_obj = var_iter.Next()
                    if not var_obj: break
                    aframe = var_obj.frame()
                    data_set_func.plotOn(aframe)
                    model.plotOn(aframe)
                    aframe.Draw()
                    self.c1.Update()
                    raw_input("Hit Enter to continue")
                    
 
            # ROOT doesn't play nicely with python always, 
            # so we have to delete by hand
            data_set_func.IsA().Destructor(data_set_func)
    
        return list_of_values

