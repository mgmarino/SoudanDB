import ROOT
from base_model import BaseModel

class GammaLineModel(BaseModel):
    def __init__(self, 
                 basevars,
                 mean,
                 sigma,
                 lifetime = None):
        BaseModel.__init__(self, basevars)



        name = str(self.get_tag()) + "_" + str(mean.getVal())
        if lifetime:
            name += "_lt_"
            name += str(lifetime.getVal()) 
       
	    # Gamma pdf
        if not lifetime:
            self.energy_pdf = ROOT.RooGaussian("gamma_line_%s" % name, 
                                               "GammaPdf_%s" % name, 
                                               basevars.get_energy(),
                                               mean, sigma)
            self.gamma_pdf = self.energy_pdf
        if lifetime:
            self.local_lifetime = ROOT.RooFormulaVar(
                                    "local_lifetime_%s" % name, 
                                    "local_lifetime_%s" % name, 
                                    "-0.693147181/@0", 
                                    ROOT.RooArgList(lifetime))
            self.time_pdf = ROOT.RooExponential("time_pdf_%s" % str(self.local_lifetime.getVal()), 
                                                 "TimePdf", 
                                                 basevars.get_time(),
                                                 self.local_lifetime)
            self.gamma_pdf = ROOT.RooProdPdf("GammaLine%s" % name, 
                                            "Gamma Line %s" % name, 
                                            self.time_pdf, 
                                            self.energy_pdf)

    def get_model(self):
        return self.gamma_pdf
        #return self.energy_pdf


class GammaLineFactory:
    created = {}

    @classmethod
    def generate(cls,mean_value, lifetime_value, basevars):
      return cls.generate(mean_value, mean_value*0.05, 0.1*mean_value, 0.05*mean_value,
                   lifetime_value, basevars)
    @classmethod
    def generate(cls,mean_value, mean_error, sigma, sigma_error, lifetime_value, basevars, name=None):
        if mean_value in cls.created.keys(): return cls.created[mean_value][0]
        if not name:
            name = str(mean_value) + "_" + str(lifetime_value)
        mean = ROOT.RooRealVar("mean_%s" % name,"mean_%s" % name, 
                               mean_value, 
                               mean_value-mean_error, 
                               mean_value+mean_error)
        sigma = ROOT.RooRealVar("sigma_%s" % name,"sigma_%s" % name, 
                                sigma, 
                                sigma - sigma_error, 
                                sigma + sigma_error)
        if lifetime_value == 0:
            lifetime = None
        else:
            lifetime = ROOT.RooRealVar("lifetime_%s" % name,
                                       "lifetime_%s" % name, 
                                       lifetime_value, 
                                       0.*lifetime_value, 
                                       1.2*lifetime_value)
        gamma_line = GammaLineModel(basevars, mean, sigma, lifetime)
        cls.created[mean_value] = (gamma_line, mean, sigma, lifetime)
        return cls.created[mean_value][0]
        
