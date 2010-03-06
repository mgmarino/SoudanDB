import ROOT
from base_model import BaseModel

class FlatModel(BaseModel):
    def __init__(self, \
                 basevars):
        BaseModel.__init__(self, basevars)

        # Flat pdf
        tag = self.get_tag()
        self.time_pdf = ROOT.RooPolynomial("time_pdf_%i" % tag, \
                                           "time_pdf_%i" % tag, \
                                           basevars.get_time())
        self.energy_pdf = ROOT.RooPolynomial("energy_pdf_%i" % tag, \
                                             "energy_pdf_%i" % tag, \
                                             basevars.get_energy())
        self.flat_pdf = ROOT.RooProdPdf("time_and_energy_pdf_%i" % tag, \
                                        "time_and_energy_pdf_%i" % tag, \
                                        self.time_pdf, \
                                        self.energy_pdf)

    def get_model(self):
        return self.flat_pdf


