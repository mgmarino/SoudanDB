import ROOT
from base_model import BaseModel
import gamma_line_model 
import background_model 
import math

def get_sigma(energy_in_eV):
    noise = 70.4843
    energy_par = 6.49228e-2
    return math.sqrt(noise*noise + 2.96*2.96*energy_par*energy_in_eV)
class FittingModel(BaseModel):
    def __init__(self, \
                 basevars,
                 use_rel = False,
                 erfc_on = False):
        BaseModel.__init__(self, basevars)
        self.initialize(basevars)

    def initialize(self, basevars):
        mean_list = [("Ge", 10.367, 0.10, 0.1, 0.04, 0), 
                     ("Ga", 9.659, 0.10, 0.1, 0.04, 0), 
                     ("Zn", 8.979, 0.1, 0.1, 0.04, 0), 
                     ("As", 11.103, 0.1, 0.1, 0.04, 0), 
                     ("Ge-Low", 1.299, 0.0, 0.1, 0.01, 0), 
                     ("ZN-Low", 1.10, 0.0, 0.1, 0.01, 0) ]
                     #("Unknown", 0.9, 0.05, 0.1, 0.04, 0), 
        
        self.gamma_list = []
        max = basevars.get_energy().getMax()
        min = basevars.get_energy().getMin()
        for name,mean,mean_error,sigma, sigma_error, atime in mean_list:
            if mean > max or mean < min: continue
            agamma = gamma_line_model.GammaLineFactory.generate(mean, mean_error, get_sigma(mean*1e3)*1e-3, 
                sigma_error, atime, basevars,name)
            self.gamma_list.append((agamma, agamma.get_model()))
          
        self.expm = background_model.FlatWithExponentialModel(basevars)
        self.exp_pdf = self.expm.get_model()
        self.final_pdf = self.exp_pdf 
        self.added_pdf = self.final_pdf
        self.saved_pdf = [] # Hack to keep this from dying
        for _,gamma in self.gamma_list:
            new_var = ROOT.RooRealVar("%s_ampl" % gamma.GetName(), 
                                      "%s_ampl" % gamma.GetName(), 
                                      0, 1)
            #self.saved_pdf.append((self.added_pdf, new_var))
            name = "%s_%s" % (self.added_pdf.GetName(), gamma.GetName())
            self.saved_pdf.append((self.added_pdf, new_var))
            self.final_pdf = ROOT.RooAddPdf(name,
                                       name, 
                                       gamma, self.added_pdf, new_var)
            self.added_pdf = self.final_pdf

    def get_model(self):
        return self.final_pdf


class LowEnergyBackgroundModel(FittingModel):
    def initialize(self, basevars):
        mean_list = [("Ge", 10.367, 0.1, 0.1, 0.02, 0), 
                     ("Ga", 9.659, 0.1, 0.1, 0.02, 0), 
                     ("Zn", 8.979, 0.1, 0.1, 0.02, 0), 
                     ("As", 11.103, 0.1, 0.1, 0.02, 0), 
                     ("Ge-Low", 1.299, 0.0, 0.1, 0.1, 0), 
                     #("Unknown", 0.9, 0.05, 0.1, 0.04, 0), 
                     ("ZN-Low", 1.10, 0.0, 0.1, 0.1, 0) ]
        
        self.gamma_list = []
        max = basevars.get_energy().getMax()
        min = basevars.get_energy().getMin()
        for name,mean,mean_error,sigma, sigma_error, atime in mean_list:
            if mean > max or mean < min: continue
            agamma = gamma_line_model.GammaLineFactory.generate(mean, 0, get_sigma(mean*1e3)*1e-3, 
                0, #get_sigma(mean*1e3)*4e-4, 
                atime, basevars,name)
            self.gamma_list.append((agamma, agamma.get_model()))
          
        self.expm = background_model.FlatWithExponentialModel(basevars)
        self.exp_pdf = self.expm.get_model()
        self.final_pdf = self.exp_pdf 
        self.added_pdf = self.final_pdf
        self.saved_pdf = [] # Hack to keep this from dying
        ratio  = 0.331511
        self.zn_ge_relative_amplitude = ROOT.RooRealVar(
                                             "l_ratio",
                                             "l_ratio",
                                             ratio/(1 + ratio))
               
        for _,gamma in self.gamma_list:
            new_var = ROOT.RooRealVar("%s_ampl" % gamma.GetName(), 
                                      "%s_ampl" % gamma.GetName(), 
                                      1e-15, 10000)
            #self.saved_pdf.append((self.added_pdf, new_var))
            self.saved_pdf.append((gamma, new_var))
            #name = "%s_%s" % (self.added_pdf.GetName(), gamma.GetName())
            #self.final_pdf = ROOT.RooAddPdf(name,
            #                           name, 
            #                           gamma, self.added_pdf, new_var)
            #self.added_pdf = self.final_pdf
        self.pdf_list = ROOT.RooArgList()
        self.coefficienct_list = ROOT.RooArgList()
        zn = self.saved_pdf[1][0]
        ge = self.saved_pdf[0][0]
        ratio_pdf = ROOT.RooAddPdf("Ge+Zn", "Ge+Zn", zn, ge, self.zn_ge_relative_amplitude)
        new_amplitude = ROOT.RooRealVar("lline_amp", "lline_amp",
                                             1e-15, 10000) 
        self.saved_pdf.append((ratio_pdf, new_amplitude))
        self.pdf_list.add(ratio_pdf)
        self.coefficienct_list.add(new_amplitude)
        #for gamma, var in self.saved_pdf:
        #    self.pdf_list.add(gamma)
        #    self.coefficienct_list.add(var)


        tag = ""
        self.exp_constant_one = ROOT.RooRealVar("expo_const_one%s" % tag,
                                            "expo_const_one%s" % tag,
                                            #1./3, 0, 500)
                                            -1./3, -100, 5)
        #self.exp_constant_one.removeMax()
        self.exp_constant_one.setError(0.5)
        self.exp_constant_time = ROOT.RooRealVar("expo_const_time_%s" % tag,
                                            "expo_const_time_%s" % tag,
                                            -0.2, -1, 0.5)

        self.exp_coef = ROOT.RooRealVar("exp_coef_%s" % tag,
                                        "exp_coef_%s" % tag,
                                        1e-15, 2000)
        self.flat_coef = ROOT.RooRealVar("flat_coef_%s" % tag,
                                         "flat_coef_%s" % tag,
                                         1e-15, 1000)
        # Flat pdf
        self.time_pdf = ROOT.RooPolynomial("time_pdf_exp_%s" % tag, 
                                           "time_pdf_exp_%s" % tag, 
                                           basevars.get_time())
        self.energy_pdf_flat = ROOT.RooPolynomial("energy_pdf_flat_%s" % tag, 
                                           "energy_pdf_flat_%s" % tag, 
                                           basevars.get_energy())
        self.energy_exp_pdf = ROOT.RooExponential("energy_pdf_exp", 
                                           "energy_pdf_exp", 
                                           basevars.get_energy(),
                                           self.exp_constant_one)
        self.pdf_list.add(self.energy_pdf_flat)
        self.coefficienct_list.add(self.flat_coef)
        self.pdf_list.add(self.energy_exp_pdf)
        self.coefficienct_list.add(self.exp_coef)


    def get_list_components(self):
        return (self.pdf_list, self.coefficienct_list)
