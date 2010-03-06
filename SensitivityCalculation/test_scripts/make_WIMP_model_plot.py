
import wimp_model
import ROOT
import re
mass_of_wimp = 60
wm = wimp_model.AllWIMPModels(energy_max=20, mass_of_wimp=mass_of_wimp, time_in_years=5)
model = wm.get_WIMP_model()
hist = model.createHistogram("hist", wm.get_energy(), \
                          ROOT.RooFit.Binning(200),\
                          ROOT.RooFit.YVar(wm.get_time(), \
                          ROOT.RooFit.Binning(40, 0, 3)))
hist.SetLineColor(4)
hist.GetXaxis().CenterTitle()
hist.GetXaxis().SetTitle("Energy (keV)")
hist.GetXaxis().SetTitleOffset(1.4)
hist.GetYaxis().CenterTitle()
hist.GetYaxis().SetTitle("Time (years)")
hist.GetYaxis().SetTitleOffset(1.4)
hist.GetZaxis().CenterTitle()
hist.GetZaxis().SetTitle("Amplitude (a.u.)")
hist.GetZaxis().SetTitleOffset(1.3)
c1 = ROOT.TCanvas()
hist.Draw("SURF")
c1.Update()
raw_input("Enter")
c1.Print("WIMPModel.eps")
