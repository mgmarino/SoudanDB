import wimp_model
import ROOT
import sys
ROOT.RooRandom.randomGenerator().SetSeed(0)
ROOT.RooMsgService.instance().setGlobalKillBelow(0)
number_of_events = 671
wm = wimp_model.AllWIMPModels(energy_max=50, mass_of_wimp=21, kilograms = 1, energy_threshold=4, time_in_years=1)
model_normal = ROOT.RooRealVar("model_normal", "model_normal", 1, 0, 1)
model = wm.get_WIMP_model_with_escape_vel()
simple_model = wm.get_simple_model()
variables = ROOT.RooArgSet(wm.get_energy(), wm.get_time())
model_extend = ROOT.RooExtendPdf("model_extend", "model_extend", model, model_normal)
flat_normal = ROOT.RooRealVar("flat_normal", "flat_normal", number_of_events, 0, 10000000)
flat_function =  wm.get_flat_model()
flat_extend = ROOT.RooExtendPdf("flat_extend", "flat_extend", flat_function, flat_normal)
print "1"
print model.getVal(variables)
print "2"
print model.getVal()
integ = model.createIntegral(ROOT.RooArgSet(wm.get_energy())).getVal()
print "3"
print integ
integ = model.createIntegral(variables).getVal()
print "4"
print integ
print model.expectedEvents(variables)

integ = model.createIntegral(ROOT.RooArgSet(wm.get_energy())).getVal()
print integ
integ = simple_model.createIntegral(ROOT.RooArgSet(wm.get_energy())).getVal()
print integ
integ = model_extend.createIntegral(variables).getVal()
print integ
print model_extend.getNorm(variables)
print model.getNorm(variables)
print model_extend.expectedEvents(variables)
print "B"
norm = wm.get_normalization().getVal()
print norm
sys.exit(0)

model = simple_model
added_pdf = ROOT.RooAddPdf("add_pdf", "add_pdf", ROOT.RooArgList(flat_function, model), ROOT.RooArgList(model_normal))
while(1):
    data = flat_function.generate(variables, number_of_events)
    data.Print()

    flat_extend.fitTo(data,\
                               ROOT.RooFit.Hesse(False),\
                               ROOT.RooFit.Minos(False))#,\
    added_pdf.fitTo(data,\
                               ROOT.RooFit.Hesse(False),\
                               ROOT.RooFit.Minos(False))#,\
    added_pdf.Print()
    frame = wm.get_energy().frame()
    frame_t = wm.get_time().frame()
    data.plotOn(frame)
    flat_extend.plotOn(frame)
    added_pdf.plotOn(frame)
    data.plotOn(frame_t)
    flat_extend.plotOn(frame_t)
    added_pdf.plotOn(frame_t)
    c1 = ROOT.TCanvas()
    frame.Draw()
    integ = model_extend.createIntegral(variables).getVal()
    events = 1-model_normal.getVal()
    print integ, events*number_of_events, integ*events*number_of_events, events*number_of_events/integ
    print norm*number_of_events*events
    print number_of_events
    c1.Update()
    raw_input("E")
    frame_t.Draw()
    c1.Update()
    raw_input("E")
