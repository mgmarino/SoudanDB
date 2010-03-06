import wimp_model
import ROOT
wm = wimp_model.AllWIMPModels(energy_max=80)
wimp_mass_list = [x*0.25 for x in range(1, 40)]
wimp_mass_list.extend(range(10, 25+1))
wimp_mass_list.extend(range(30, 100+1, 10))
wimp_mass_list.extend(range(200, 1000+1, 100))

c1 = ROOT.TCanvas()
precision = ROOT.RooNumIntConfig.defaultConfig()
#precision.setEpsAbs(1e-15)
#precision.setEpsRel(1e-30)
wm.get_time().setMax(1)
wm.get_energy().setMax(20)
wm.get_energy().setMin(0.4)
for i in wimp_mass_list: 
    print "Wimp Mass: ", i
    test = wm.get_WIMP_model(i)
    frame = wm.get_energy().frame()
    integral = test.createIntegral(ROOT.RooArgSet(wm.get_time(), wm.get_energy()),\
                                   ROOT.RooFit.NumIntConfig(precision))
    print integral.getVal()
    test.plotOn(frame)
    frame.Draw() 
    c1.Update()
    raw_input("")
