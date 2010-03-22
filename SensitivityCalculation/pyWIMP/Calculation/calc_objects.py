#
# calc_object exports classes which can be 
# used for calculation of sensitivities
#
import ROOT
import ExclusionCalculation as ec
import OscillationSensitivityCalculation as osc
import DataCalculation as dat

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
        return {'total_time' : ('Total time (year)', 5),
                'threshold' : ('Threshold (keV)', 1),
                'energy_max' : ('Maximum energy (keV)', 50),
                'mass_of_detector' : ('Mass of detector (kg)', 1),
                'background_rate' : ('Background rate (counts/keV/kg/day)', 0.1),
                'wimp_mass' : ('WIMP mass (GeV/c^-2)', 10),
                'confidence_level' : ('Confidence level (0 -> 1)', 0.9),
                'variable_quenching' : ('Set to use variable quenching', False),
                'constant_time' : ('Set time as constant', False),
                'constant_energy' : ('Set energy as constant', False),
                'show_plots' : ('Show plot results of fit', False),
                'print_out_plots' : ("""Print plot results of fit to eps format.  
This will cause the program to continue
instead of stopping once a plot is made.
Batch mode will be set so that no plot
will be displayed during the program.
                                     """, False),
                'debug' : ('Set debug flag, enables verbose output', False) }
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
        if self.debug:
            self.print_level = 3
            self.verbose = True
        else:
            self.print_level = -1
            self.verbose = False

    # overload this function for derived classes.
    def initialize(self):

        if self.is_initialized: return
        from pyWIMP.DMModels.wimp_model import WIMPModel
        from pyWIMP.DMModels.base_model import BaseVariables
        from pyWIMP.DMModels.flat_model import FlatModel

        self.total_counts = int(self.mass_of_detector*
                                self.background_rate*
                                (self.energy_max-self.threshold)*
                                self.total_time*365)
        if not self.basevars:
            self.basevars = BaseVariables(time_beginning=0,
                time_in_years=self.total_time,
                energy_threshold=self.threshold,
                energy_max=self.energy_max)

        self.variables = ROOT.RooArgSet()
        if self.constant_time:
            self.basevars.get_time().setVal(0)
            self.basevars.get_time().setConstant(True)
        else:
            self.variables.add(self.basevars.get_time())
        if not self.constant_energy:
            self.variables.add(self.basevars.get_energy())

        self.model_normal = ROOT.RooRealVar("model_normal", 
                                            "model_normal", 
                                            1, -10, 1000)
        self.wimpClass = WIMPModel(self.basevars,
            mass_of_wimp=self.wimp_mass,
            kilograms = self.mass_of_detector,
            constant_quenching=(not self.variable_quenching))

        self.flatClass = FlatModel(self.basevars)

        self.calculation_class = \
            ec.ExclusionCalculation(self.exit_manager)
 
        # This is where we define our models
        self.background_model =  self.flatClass.get_model()
        self.model = self.wimpClass.get_model()
        self.norm = self.wimpClass.get_normalization().getVal()
        self.is_initialized = True

        self.background_normal = ROOT.RooRealVar("flat_normal", \
                                                 "flat_normal", \
                                                 self.total_counts, \
                                                 -10,\
                                                 3*self.total_counts)
        self.background_extend = ROOT.RooExtendPdf("background_extend", \
                                                   "background_extend", \
                                                   self.background_model, \
                                                   self.background_normal)
        self.model_extend = ROOT.RooExtendPdf("model_extend", \
                                               "model_extend", \
                                               self.model, \
                                               self.model_normal)

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
        This function runs from the base class, so derived classes should
        not need to overload it.
        """
        import pickle
        import signal
        import os

        ROOT.RooRandom.randomGenerator().SetSeed(0)
        self.initialize()
        ROOT.gROOT.SetBatch()
        if self.show_plots or self.print_out_plots:
            self.calculation_class.set_canvas(ROOT.TCanvas())
        if self.show_plots and not self.print_out_plots:
            ROOT.gROOT.SetBatch(0)

        if not self.debug:
            ROOT.RooMsgService.instance().setSilentMode(True)
            ROOT.RooMsgService.instance().setGlobalKillBelow(3)

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

        print norm_integral_val
        if norm_integral_val == 0.0:
            print "Integral defined as 0, meaning it is below numerical precision"
            print "Aborting further calculation"
            write_pipe.write(pickle.dumps({}))
            write_pipe.close()
            return
 
        # Set up signal handler
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGUSR1, self.exit_manager.exit_handler)

       

        self.calculation_class.set_debug(self.debug)
        self.calculation_class.set_show_plots(self.show_plots)
        self.calculation_class.set_print_out_plots(self.print_out_plots)
        self.calculation_class.set_plot_base_name(
            "%s WIMP Mass: %g GeV" % (self.__class__.__name__,
                                  self.wimp_mass))
        results_list = \
            self.calculation_class.scan_confidence_value_space_for_model(
                self.fitting_model, 
                self.data_set_model, 
                self.test_variable, 
                self.norm, 
                self.variables, 
                self.total_counts, 
                self.number_iterations, 
                self.confidence_level)

        write_pipe.write(pickle.dumps(results_list))
        write_pipe.close()

class DataExclusion(WIMPModel):
    def get_requested_values(cls):
        adict = WIMPModel.get_requested_values()
        del adict['constant_energy']
        del adict['constant_time']
        del adict['background_rate']
        adict['data_file'] = ('Name of data root file', 'temp.root')
        adict['object_name'] = ("""Name of object inside data file. 
This can be a:                                             
                                                                
TH1: the bins will be interprected as energy. 
A RooDataHist will be used to generate a binned fit.  
                                                                
TTree: with branches, 'ee_energy', 'time', 'efficiency', plus others.
'time' and ee_energy are both optional, it is assumed that if they
don't exist that time and energy are constant.
'efficiency' is optional, but when present will adjust the weight of each
entry to 1/efficiency in the RooDataSet.
A RooDataSet will be used to generate an unbinned fit. 
                                """, 'output_data')
        adict['data_set_cuts'] = ("""String of cuts to apply. 
This only applies if the object passed
in is a TTree (see object_name).  These cuts will be used to generate
a subset of the TTree and pass into RooDataSet.
                                  """, '')
        return adict
    get_requested_values = classmethod(get_requested_values)
    def initialize(self):
        # The background model is the same, but now we switch it to the data model
        from pyWIMP.DMModels.low_energy_background import LowEnergyBackgroundModel
        from pyWIMP.DMModels.base_model import BaseVariables
        from pyWIMP.DMModels.wimp_model import WIMPModel
        self.total_counts = None
        open_file = ROOT.TFile(self.data_file)
        self.workspace = open_file.Get(self.object_name)
        # Do some introspection, we can handle TH1s, and RooAbsData 
        self.basevars = BaseVariables(time_beginning=0,
            time_in_years=self.total_time,
            energy_threshold=self.threshold,
            energy_max=self.energy_max,
            use_tag=False)

        self.variables = ROOT.RooArgSet()

        if self.workspace.InheritsFrom(ROOT.TH1.Class()):
            self.variables.add(self.basevars.get_energy())
            self.basevars.get_time().setVal(0)
            self.basevars.get_time().setConstant(True)

            self.data_set_model = ROOT.RooDataHist("data", "data", 
                                    ROOT.RooArgList(self.basevars.get_energy()),
                                    self.workspace)
        elif self.workspace.InheritsFrom(ROOT.TTree.Class()):
            # Default to setting them to constant.
            self.basevars.get_time().setVal(0)
            self.basevars.get_time().setConstant(True)
            self.basevars.get_energy().setVal(0)
            self.basevars.get_energy().setConstant(True)

            branches = self.workspace.GetListOfBranches()
            efficiency = 1.
            branch_arg_list = []

            for i in range(branches.GetEntries()):
                branch_name = branches[i].GetName()
                if branch_name == "ee_energy": 
                    self.basevars.get_energy().setConstant(False)
                    self.variables.add(self.basevars.get_energy())
                    branch_arg_list.append((self.basevars.get_energy(), 
                                            branch_name))
                if branch_name == "time": 
                    self.basevars.get_time().setConstant(False)
                    self.variables.add(self.basevars.get_time())
                    branch_arg_list.append((self.basevars.get_time(), 
                                            branch_name))
                elif branch_name == "efficiency":
                    efficiency = branch_name 

            if not self.data_set_cuts and not efficiency:
                # Load the DataSet the easy way
                self.data_set_model = ROOT.RooDataSet("data", "data", 
                                        self.workspace,
                                        self.variables)
            else:
                # Otherwise, we have to get the correct events,
                # which requires stepping through all events
                self.data_set_model = ROOT.RooDataSet("data", "data", 
                                        self.variables)
                # Get an event list with the correct cut events
                ROOT.gROOT.cd()
                el = ROOT.TEventList("el", "el")
                cuts = self.data_set_cuts
                iter = self.variables.createIterator()
                while 1: 
                    obj = iter.Next()
                    if not obj: break
                    cuts += " && ((%s <= %f) && (%s >= %f))" % (obj.GetName(),
                                                                obj.getMax(),
                                                                obj.GetName(),
                                                                obj.getMin())
                self.workspace.Draw(">>%s" % el.GetName(), cuts, "goff")
                event_list = [el.GetEntry(i) for i in range(el.GetN())] 
                #event_list = [i for i in range(self.workspace.GetEntries())] 
                for j in event_list: 
                    self.workspace.GetEntry(j)
                    eff_val = 1.
                    if efficiency: 
                        eff_val = getattr(self.workspace, efficiency)
                    for val in branch_arg_list: 
                        val[0].setVal(getattr(self.workspace, val[1]))
                    if eff_val != 0: self.data_set_model.add(self.variables, 1./eff_val)
                     
        else:
            print "Requested: %s, isn't a TTree or TH1!" % self.data_set_name
            raise TypeError

        print "Data set has %i entries." % self.data_set_model.sumEntries()

        self.model_normal = ROOT.RooRealVar("model_normal", 
                                            "model_normal", 
                                            1, 0, 100*self.data_set_model.sumEntries())
        self.wimpClass = WIMPModel(self.basevars,
            mass_of_wimp=self.wimp_mass,
            kilograms = self.mass_of_detector,
            constant_quenching=(not self.variable_quenching))

        # This is where we define our models
        self.model = self.wimpClass.get_model()
        #self.model = self.wimpClass.get_simple_model()
        self.norm = self.wimpClass.get_normalization().getVal()
        self.is_initialized = True

        self.background_normal = ROOT.RooRealVar("flat_normal", 
                                                 "flat_normal", 
                                                 0,
                                                 3)
        self.model_extend = ROOT.RooExtendPdf("model_extend", 
                                               "model_extend", 
                                               self.model, 
                                               self.model_normal)

        self.calculation_class = \
            dat.DataCalculation(self.exit_manager)
        self.low_energy = LowEnergyBackgroundModel(self.basevars)
        self.low_energy_model = self.low_energy.get_model()
        self.background_normal.setMax(2*self.data_set_model.sumEntries())
        self.background_extend = ROOT.RooExtendPdf("background_extend", 
                                                   "background_extend", 
                                                   self.low_energy_model, 
                                                   self.background_normal)
        self.added_pdf = ROOT.RooAddPdf("b+s", 
                                        "Background + Signal", 
                                        ROOT.RooArgList(
                                        self.background_extend, 
                                        self.model_extend))
        self.test_variable = self.model_normal
        self.fitting_model = self.added_pdf
        #getattr(self.workspace, 'import')(self.fitting_model)
        


class OscillationSignalDetection(WIMPModel):
    def get_requested_values(cls):
        adict = WIMPModel.get_requested_values()
        del adict['constant_energy']
        del adict['constant_time']
        del adict['wimp_mass']
        del adict['variable_quenching']
        adict['model_amplitude'] = ('Initial model amplitude', 0.1)
        return adict
    get_requested_values = classmethod(get_requested_values)

    # overload this function for derived classes.
    def initialize(self):

        if self.is_initialized: return
        from pyWIMP.DMModels.base_model import BaseVariables
        from pyWIMP.DMModels.flat_model import FlatModel
        from pyWIMP.DMModels.oscillation_model import OscillationModel
        self.basevars = BaseVariables(time_beginning=0,\
            time_in_years=self.total_time,\
            energy_threshold=self.threshold,\
            energy_max=self.energy_max)

        self.oscClass = OscillationModel(self.basevars)

        self.flatClass = FlatModel(self.basevars)


        self.calculation_class = \
            osc.OscillationSensitivityCalculation(self.exit_manager)

        self.variables = ROOT.RooArgSet()
        self.variables.add(self.basevars.get_time())

        self.basevars.get_energy().setVal(0)
        self.basevars.get_energy().setConstant(True)

        # This is where we define our models
        self.background =  self.flatClass.get_model()
        self.model = self.oscClass.get_model()
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
                                            self.model_amplitude, \
                                            0, 1)

        self.total_fit_counts = ROOT.RooRealVar("total_fit_counts", \
                                            "total_fit_counts", \
                                            self.total_counts, \
                                            0, 3*self.total_counts)
        self.added_pdf = ROOT.RooAddPdf(\
                                "added_pdf",\
                                "Fit Model",\
                                self.model,\
                                self.background,\
                                self.model_normal)

        self.model_extend = ROOT.RooExtendPdf("model_extend",\
                                              "Signal + Background",\
                                              self.added_pdf,\
                                              self.total_fit_counts)

        self.test_variable = self.model_normal
        self.data_set_model = self.background_model
        self.fitting_model = self.model_extend 


