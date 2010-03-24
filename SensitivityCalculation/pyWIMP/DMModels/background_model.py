import ROOT
from base_model import BaseModel

class FlatWithExponentialModel(BaseModel):
    def __init__(self, 
                 basevars):
        BaseModel.__init__(self, basevars)

        tag = str(self.get_tag())
        self.exp_constant = ROOT.RooRealVar("expo_const_%s" % tag,
                                            "expo_const_%s" % tag,
                                            -4, 0.5)
        self.exp_constant_time = ROOT.RooRealVar("expo_const_time_%s" % tag,
                                            "expo_const_time_%s" % tag,
                                            -0.2, -1, 0.5)

        self.energy_constant = ROOT.RooRealVar("energy_const_%s" % tag,
                                               "energy_const_%s" % tag,
                                               0, 1)
        # Flat pdf
        self.time_pdf = ROOT.RooPolynomial("time_pdf_exp_%s" % tag, 
                                           "time_pdf_exp_%s" % tag, 
                                           basevars.get_time())
        self.energy_pdf_flat = ROOT.RooPolynomial("energy_pdf_flat_%s" % tag, 
                                           "energy_pdf_flat_%s" % tag, 
                                           basevars.get_energy())
        #self.time_pdf = ROOT.RooExponential("time_pdf_exp", 
        #                                   "time_pdf_exp", 
        #                                   basevars.get_time(),
        #                                   self.exp_constant_time)
        self.energy_pdf_exp = ROOT.RooExponential("energy_pdf_exp_%s" % tag, 
                                             "energy_pdf_exp_%s" % tag, 
                                             basevars.get_energy(),
                                             self.exp_constant)
        self.energy_pdf = ROOT.RooAddPdf("energy_pdf_%s" % tag, 
                                         "energy_pdf_%s" % tag, 
                                         self.energy_pdf_exp,
                                         self.energy_pdf_flat, 
                                         self.energy_constant)
        #self.energy_pdf = self.energy_pdf_flat
        self._pdf = ROOT.RooProdPdf("time_and_energy_exp_pdf_%s" % tag, 
                                        "time_and_energy_exp_pdf_%s" % tag, 
                                        self.time_pdf, 
                                        self.energy_pdf)

    def get_model(self):
        return self._pdf
