
class AllWIMPModels:
    def __init__(self, time_beginning=0, time_in_years=5, energy_threshold=0, energy_max=20,\
                 mass_of_wimp=20, kilograms=1):
        import ROOT
        import pyWIMP.WIMPPdfs as pdfs  
        self.time = ROOT.RooRealVar("time", "Time",time_beginning,\
                    time_in_years, "years") 
        self.ee_energy = ROOT.RooRealVar("ee_energy", "ee_energy", \
                         energy_threshold, energy_max, "keV")
        self.flat_normal = ROOT.RooRealVar("flat_normal", "flat_normal", \
                         0, 10000 )

        # constant quenching
        self.quenching = ROOT.RooRealVar("quenching", "quenching", 0.2)
        #self.dQ_over_dE = ROOT.RooFormulaVar("dQ_over_dE", "#frac{dQ}{dE}",\
        #                  "1./@0", ROOT.RooArgList(self.quenching))

        self.threshold = ROOT.RooRealVar("threshold", "threshold", \
                         energy_threshold)
        self.kilograms = ROOT.RooRealVar("kilograms", "kilograms", \
                         kilograms)
        self.energy_max = ROOT.RooRealVar("energy_max", "energy_max", \
                          energy_max)
        #self.energy = ROOT.RooFormulaVar("energy", "Energy", \
        #              "@0/@1", ROOT.RooArgList(self.ee_energy, \
        #              self.quenching))

        self.energy = ROOT.RooFormulaVar("energy", "Energy", \
                      "TMath::Power(@0/0.14,0.840336)", \
                      ROOT.RooArgList(self.ee_energy))
        self.dQ_over_dE = ROOT.RooFormulaVar("dQ_over_dE", "#frac{dQ}{dE}",\
                          "4.38523*TMath::Power(@0, 0.1596638655)", ROOT.RooArgList(self.ee_energy))

        self.v_sub_E_sub_0 = ROOT.RooRealVar("v_sub_E_sub_0", \
                        "Constant in Velocity Function", 244, "km s^-1") 
        self.v_sub_E_sub_1 = ROOT.RooRealVar("v_sub_E_sub_1", \
                        "Modulation Amplitude in Velocity Function", 15, \
                        "km s^-1") 
        self.atomic_mass_of_target = ROOT.RooRealVar("atomic_mass_of_target", \
                                "Atomic Mass of Target", 68/0.932, "amu") 
                                #"Atomic Mass of Target", 68/0.932, "amu") 
        self.density_of_dark_matter = ROOT.RooRealVar("density_of_dark_matter", \
                           "Density of Dark Matter", 0.4, "Gev c^-2 cm^-3") 
        self.speed_of_light = ROOT.RooRealVar("speed_of_light", \
                         "Speed of Light", 299792.458, "km s^-1") 
        self.v_sub_0 = ROOT.RooRealVar("v_sub_0", \
                  "Base Velocity", 230, "km s^-1") 
        self.v_sub_esc = ROOT.RooRealVar("v_sub_esc", \
                  "Escape Velocity", 650, "km s^-1") 
        self.mass_of_target = ROOT.RooFormulaVar("mass_of_target", \
                         "Mass of Target", "0.932*@0", \
                         ROOT.RooArgList(self.atomic_mass_of_target)) 
        self.mass_of_target.setUnit("GeV c^02")

        # Following is for the Form Factors
        self.q = ROOT.RooFormulaVar("q", "Momentum Transfer",\
                   "sqrt(2*@0*@1)/197.3", ROOT.RooArgList(\
                   self.energy, self.mass_of_target))
        self.q.setUnit("fm^-1")

        self.r_sub_n = ROOT.RooFormulaVar("r_sub_n", "Effective Nuclear Radius",\
                         "1.14*TMath::Power(@0, 1./3.)", ROOT.RooArgList(\
                         self.atomic_mass_of_target))
        self.r_sub_n.setUnit("fm")

        self.s = ROOT.RooRealVar("s", "Nuclear Skin Thickness",0.9)
        self.s.setUnit("fm")
        
        self.r_sub_0 = ROOT.RooFormulaVar("r_sub_0", "Nuclear Radius",\
                         "(0.3 + 0.91*TMath::Power(@0, 1./3.))", \
                         ROOT.RooArgList(self.mass_of_target))
        self.r_sub_0.setUnit("fm")
        self.q_sub_0 = ROOT.RooFormulaVar("q_sub_0", "Coherence Energy",\
                         "1.5*(197.3*197.3)/(@0*@1*@1)", \
                         ROOT.RooArgList(self.mass_of_target,\
                         self.r_sub_0))
        self.q_sub_0.setUnit("keV")

        self.mass_of_wimp = ROOT.RooRealVar("mass_of_wimp", \
                       "Mass of Wimp", mass_of_wimp, "GeV c^{-2}") 
 

        self.R_sub_0 = ROOT.RooFormulaVar("R_sub_0", "Base Rate",\
                       "365*@4*@5*503.4/(@0*@1)*(@2/0.4)*(@3/230.)", \
                       ROOT.RooArgList(self.mass_of_target, self.mass_of_wimp,\
                       self.density_of_dark_matter, self.v_sub_0,\
                       self.kilograms, self.dQ_over_dE))

        self.R_sub_0.setUnit("pb^{-1} yr^{-1}") 
        
        # The following is dealing with the generation of the dR/dQ
        # NO escape velocity!
        

        self.r = ROOT.RooFormulaVar("r", "Lewin/Smith r",\
                       "4*@0*@1/((@0+@1)**2)", ROOT.RooArgList(\
                       self.mass_of_wimp, self.mass_of_target))

        self.E_sub_0 = ROOT.RooFormulaVar("E_sub_0", "Lewin/Smith E_sub_0",\
                       "0.5e6*@0*((@1/@2)**2)", ROOT.RooArgList(\
                       self.mass_of_wimp, self.v_sub_0, self.speed_of_light))
        # The following is for the total rate from Jungman, including
        # an exponential form factor

 
        self.normalization = ROOT.RooFormulaVar("normalization",\
                       "Normalization Constant to WIMP-nucleon xs", \
                       "((0.932/(@0*@1/(@0+@1)))**2)*(1/@2)**2",\
                        ROOT.RooArgList(self.mass_of_target,\
                        self.mass_of_wimp, self.atomic_mass_of_target)) 
        self.normalization.setUnit("pb pb^{-1}")


        self.v_sub_E = pdfs.MGMWimpTimeFunction("v_sub_E", \
                  "Velocity of the Earth",\
                  self.v_sub_E_sub_0, self.v_sub_E_sub_1, self.time) 
        self.v_sub_E.setUnit( self.v_sub_E_sub_0.getUnit() )

        self.v_sub_min = ROOT.RooFormulaVar("v_sub_min", \
                    "Minimum Velocity of Minimum Energy", \
                    "sqrt(@0/(@1*@2))*@3", \
                    ROOT.RooArgList(self.energy, self.E_sub_0, self.r,\
                                    self.v_sub_0))
        self.v_sub_min.setUnit( self.speed_of_light.getUnit() )
        
        # Woods-Saxon/Helm
        # The crazy expansion is to deal with poor numerical estimates below a certain
        # value
        self.woods_saxon_helm_ff_squared = pdfs.MGMWimpHelmFFSquared(\
          "woods_saxon_helm_ff_squared",\
          "Helm FF^{2} ",\
          self.q, self.r_sub_n, self.s)

        # Exponential 
        self.exponential_ff_squared = ROOT.RooGenericPdf(\
          "exponential_ff_squared",\
          "Exponential Form Factor squared",\
          "exp(-@0/@1)",\
          ROOT.RooArgList(self.energy, self.q_sub_0))

       
        self.final_function = pdfs.MGMWimpDiffRatePdf("WIMPPDF_With_Time", \
                         "WIMP Pdf", \
                         self.v_sub_0, self.v_sub_min, \
                         self.v_sub_E, self.R_sub_0, \
                         self.E_sub_0, self.r, self.woods_saxon_helm_ff_squared)

        self.final_function_with_escape = pdfs.MGMWimpDiffRateEscapeVelPdf(\
                         "WIMPPDF_With_Time_And_Escape_Vel", \
                         "WIMP Pdf (esc velocity)", \
                         self.v_sub_0, self.v_sub_min, \
                         self.v_sub_E, self.R_sub_0, \
                         self.E_sub_0, self.r, \
                         self.v_sub_esc, self.woods_saxon_helm_ff_squared)

        self.final_function_with_escape_no_ff = pdfs.MGMWimpDiffRateEscapeVelPdf(\
                         "WIMPPDF_With_Time_And_Escape_Vel", \
                         "WIMP Pdf (esc velocity)", \
                         self.v_sub_0, self.v_sub_min, \
                         self.v_sub_E, self.R_sub_0, \
                         self.E_sub_0, self.r, \
                         self.v_sub_esc)

        # Flat pdf
        self.time_pdf = ROOT.RooPolynomial("time_pdf", "time_pdf", self.time)
        self.energy_pdf = ROOT.RooPolynomial("energy_pdf", "energy_pdf", self.energy)
        self.flat_pdf = ROOT.RooProdPdf("time_and_energy_pdf", \
                    "time_and_energy_pdf", \
                    self.time_pdf, self.energy_pdf)
 
        self.simple_model = ROOT.RooGenericPdf("simple model", "Lewin/Smith simple model",\
                         "0.751*@3/(@1*@2)*exp(-0.561*@0/(@1*@2))", \
                         ROOT.RooArgList(self.energy, \
                         self.E_sub_0, self.r,self.R_sub_0))
       
    def get_simple_model(self):
        return self.simple_model

    def get_velocity_earth(self):
        return self.v_sub_E

    def get_energy(self):
        return self.ee_energy

    def get_time(self):
        return self.time

    def get_normalization(self):
        return self.normalization

    def get_helm_form_factor(self):
        return self.woods_saxon_helm_ff_squared

    def get_exponential_form_factor(self):
        return self.exponential_ff_squared
    
    def get_WIMP_model(self, mass_of_wimp=None):
        if mass_of_wimp: self.mass_of_wimp.setVal(mass_of_wimp)
        return self.final_function

    def get_WIMP_model_with_escape_vel(self, mass_of_wimp=None):
        if mass_of_wimp: self.mass_of_wimp.setVal(mass_of_wimp)
        return self.final_function_with_escape

    def get_WIMP_model_with_escape_vel_no_ff(self, mass_of_wimp=None):
        if mass_of_wimp: self.mass_of_wimp.setVal(mass_of_wimp)
        return self.final_function_with_escape_no_ff
    def get_flat_model(self):
        return self.flat_pdf




