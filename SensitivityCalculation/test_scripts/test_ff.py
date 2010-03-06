import pyWIMP.DMModels.wimp_model as wimp_model
import ROOT
import re
#ROOT.gROOT.SetBatch()
mass_of_wimp = 50
wm = wimp_model.AllWIMPModels(energy_max=2*mass_of_wimp, mass_of_wimp=mass_of_wimp, time_in_years=1)
c1 = ROOT.TCanvas()
c1.SetLogy()
#test = ROOT.MGMWimpHelmFFSquared("model", "model", q, r, s)
#energy = q
test = wm.get_helm_form_factor()
test1 = wm.get_WIMP_model()
test2 = wm.get_WIMP_model_with_escape_vel()
test3 = wm.get_WIMP_model_with_escape_vel_no_ff()
energy = wm.get_energy()
time = wm.get_time()
frame = energy.frame()
energy.setVal(5)
time.setVal(0.25)
print test1.getVal(), test2.getVal(), test3.getVal(), test.getVal()
variables = ROOT.RooArgSet(wm.get_energy(), wm.get_time())

integral = test1.createIntegral(variables)
orig = integral.getVal()

integral = test.createIntegral(variables)
ff_int = integral.getVal()

integral = test2.createIntegral(variables)
orig_esc_int = integral.getVal()

integral = test3.createIntegral(variables)
simple_int = integral.getVal()

print orig, orig_esc_int, simple_int, ff_int
print test1.expectedEvents(variables)
print test2.expectedEvents(variables)
print test3.expectedEvents(variables)
test2.SetTitle("WIMP Model - escape velocity")
test1.SetTitle("WIMP Model - no escape velocity")
test3.SetTitle("WIMP Model - escape velocity, no form factor")
test2.plotOn(frame, ROOT.RooFit.LineStyle(9),ROOT.RooFit.FillColor(10),\
                    ROOT.RooFit.Normalization(orig_esc_int, ROOT.RooAbsReal.Raw))
test1.plotOn(frame, ROOT.RooFit.LineStyle(3),ROOT.RooFit.FillColor(10),\
                    ROOT.RooFit.Normalization(orig, ROOT.RooAbsReal.Raw))
test3.plotOn(frame, ROOT.RooFit.LineStyle(1),ROOT.RooFit.FillColor(10),\
                    ROOT.RooFit.Normalization(simple_int, ROOT.RooAbsReal.Raw))
#together_again.plotOn(frame,\
#                    ROOT.RooFit.Normalization(orig_time_ff, ROOT.RooAbsReal.Raw),\
#                    ROOT.RooFit.Precision(1e-10))
frame.SetMaximum(100)
frame.SetMinimum(1e-10)
frame.GetXaxis().SetTitle("Energy (keV)")
frame.GetXaxis().CenterTitle()
frame.GetYaxis().SetTitle("#frac{dR}{dE} #sigma^{-1} (counts/keV/kg/yr/pb)")
frame.GetYaxis().SetTitleOffset(1.35)
frame.GetYaxis().CenterTitle()
frame.SetTitle("WIMP Mass %g GeV" % mass_of_wimp)
ROOT.gStyle.SetOptTitle(1)
c1.SetLeftMargin(0.13)
frame.Draw()
alist = c1.GetListOfPrimitives()
legend = ROOT.TLegend(0.5, 0.67, 0.88, 0.88)
for item in alist:
    match = re.match("Projection of (.*)", item.GetTitle())
    if not match: continue
    item.SetTitle(match.group(1))
    legend.AddEntry(item)
legend.Draw()
c1.Update()
raw_input("Enter")
c1.Print("wimpMass%i.root" % mass_of_wimp)
c1.Print("wimpMass%i.eps" % mass_of_wimp)
