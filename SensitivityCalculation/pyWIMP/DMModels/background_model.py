import ROOT
from base_model import BaseModel
import pyWIMP.WIMPPdfs as pdfs

class FlatWithExponentialModel(BaseModel):
    def __init__(self, 
                 basevars):
        BaseModel.__init__(self, basevars)

        tag = str(self.get_tag())
        self.exp_constant_one = ROOT.RooRealVar("expo_const_one%s" % tag,
                                            "expo_const_one%s" % tag,
                                            #1./3, 0, 500)
                                            -1./3, -500, 0)
        #self.exp_constant_one.removeMax()
        self.exp_constant_one.setError(0.5)
        self.exp_constant_time = ROOT.RooRealVar("expo_const_time_%s" % tag,
                                            "expo_const_time_%s" % tag,
                                            -0.2, -1, 0.5)

        self.energy_constant = ROOT.RooRealVar("energy_const_%s" % tag,
                                               "energy_const_%s" % tag,
                                               0, 1000)
        self.energy_constant_two = ROOT.RooRealVar("energy_const_%s" % tag,
                                               "energy_const_%s" % tag,
                                               0, 1000)
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
        #self.energy_pdf = pdfs.MGMPolyPlusExponential(
        #                                 "energy_pdf_%s" % tag, 
        #                                 "energy_pdf_%s" % tag, 
        #                                 basevars.get_energy(),
        #                                 self.exp_constant_one,
        #                                 self.energy_constant)
        self.energy_pdf = ROOT.RooAddPdf(
                                          "energy_pdf_%s" % tag, 
                                          "energy_pdf_%s" % tag, 
                                          ROOT.RooArgList(self.energy_pdf_flat,
                                          self.energy_exp_pdf),
                                          ROOT.RooArgList(self.energy_constant,
                                          self.energy_constant_two))
        #self.energy_pdf = self.energy_pdf_flat
        self._pdf = ROOT.RooProdPdf("time_and_energy_exp_pdf_%s" % tag, 
                                        "time_and_energy_exp_pdf_%s" % tag, 
                                        self.time_pdf, 
                                        self.energy_pdf)
        self._pdf = self.energy_pdf

    def get_model(self):
        return self._pdf
