import ROOT
from base_model import BaseModel

class GammaLineModel(BaseModel):
    def __init__(self, \
                 basevars,\
                 mean,\
                 sigma,\
                 lifetime = None):
        BaseModel.__init__(self, basevars)



        name = str(mean.getVal())
        if lifetime:
            name += "_lt_"
            name += str(lifetime.getVal()) 
       
        if not lifetime:
            # Choose infinite lifetime
            self.local_lifetime = ROOT.RooRealVar("local_lifetime_%s" % name, \
                                                  "local_lifetime_%s" % name, \
                                                  0)
        else:
            self.local_lifetime = ROOT.RooFormulaVar(
                                    "local_lifetime_%s" % name, \
                                    "local_lifetime_%s" % name, \
                                    "-0.693147181/@0", \
                                    ROOT.RooArgList(lifetime))
            
	    # Gamma pdf
        self.energy_pdf = ROOT.RooGaussian("gamma_line_%s" % str(mean.getVal()), \
                                           "GammaPdf", \
                                           basevars.get_energy(),\
                                           mean, sigma)
        self.time_pdf = ROOT.RooExponential("time_pdf_%s" % str(self.local_lifetime.getVal()), \
                                             "TimePdf", \
                                             basevars.get_time(),\
                                             self.local_lifetime)
        self.gamma_pdf = ROOT.RooProdPdf("GammaLine%s" % str(mean.getVal()), \
                                        "Gamma Line %s" % str(mean.getVal()), \
                                        self.time_pdf, \
                                        self.energy_pdf)

    def get_model(self):
        return self.gamma_pdf


class GammaLineFactory:
    created = {}

    @classmethod
    def generate(cls,mean_value, lifetime_value, basevars):
        if mean_value in cls.created.keys(): return cls.created[mean_value][0]
        name = str(mean_value) + "_" + str(lifetime_value)
        mean = ROOT.RooRealVar("mean_%s" % name,"mean", \
                               mean_value, \
                               0.9*mean_value, \
                               1.1*mean_value)
        sigma = ROOT.RooRealVar("sigma_%s" % name,"sigma", \
                                0.01*mean_value, \
                                0, \
                                0.1*mean_value)
        if lifetime_value == 0:
            lifetime = None
        else:
            lifetime = ROOT.RooRealVar("lifetime_%s" % name,\
                                       "lifetime", \
                                       lifetime_value, \
                                       0.*lifetime_value, \
                                       1.2*lifetime_value)
        gamma_line = GammaLineModel(basevars, mean, sigma, lifetime)
        cls.created[mean_value] = (gamma_line, mean, sigma, lifetime)
        return cls.created[mean_value][0]
        
