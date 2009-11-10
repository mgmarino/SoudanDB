import ROOT
class BaseCalculation:

    def __init__(self, exit_manager):
        self.exit_manager = exit_manager
        self.retry_error = {'again' : True} 

    def scan_confidence_value_space_for_model(self, \
                                              model, \
                                              data_model, \
                                              model_amplitude, \
                                              mult_factor,\
                                              variables, \
                                              number_of_events,\
                                              number_iterations, \
                                              cl,\
                                              show_plots = False,\
                                              debug_output = False):
    
        print_level = -1
        verbose = debug_output
        if debug_output: print_level = 3

        list_of_values = []
        i = 0
        confidence_value = ROOT.TMath.ChisquareQuantile(cl, 1) 
        while i < number_iterations:
            if debug_output:
                print "Process %s: Iteration (%i) of (%i)" \
                    % (os.getpid(), i+1, number_iterations)
            # Generate the data, use Extended flag
            # because the number_of_events is just
            # an expected number.
            model_amplitude.setVal(0)
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
                model_amplitude, \
                confidence_value/2,\
                mult_factor,\
                print_level,\
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
    
            if show_plots:
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

