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
        for _,gamma in self.gamma_list:
            new_var = ROOT.RooRealVar("%s_ampl" % gamma.GetName(), 
                                      "%s_ampl" % gamma.GetName(), 
                                      0, 1)
            self.saved_pdf.append((self.added_pdf, new_var))
            name = "%s_%s" % (self.added_pdf.GetName(), gamma.GetName())
            self.final_pdf = ROOT.RooAddPdf(name,
                                       name, 
                                       gamma, self.added_pdf, new_var)
            self.added_pdf = self.final_pdf

       

