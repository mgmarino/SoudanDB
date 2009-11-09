
def update_pulser_data_for_rundoc(run_doc):
    import ROOT
    # check to see if we need to update
    if run_doc.pulser_data.sigma:
        return (run_doc, False)
    # following shuts off all messages from MINUIT.
    ROOT.RooMsgService.instance().setSilentMode(True)
    open_file = ROOT.TFile(run_doc.output_data_file_tier_3.low_energy.pfn)
    main_tree = open_file.Get("wf_analysis") 
    coinc_tree = open_file.Get("event_coincidence") 
    main_tree.AddFriend(coinc_tree)
    el = ROOT.TEventList("tempList", "tempList")
    main_tree.Draw(">>%s" % el.GetName(), "channel==0 && (event_coincidence.coincidence & 0x80)", "goff")
    energyRV = ROOT.RooRealVar ("energy", "energy", 2.3, 0, 4)
    sigmaRV = ROOT.RooRealVar("sigma", "sigma", .1, 0.007, 0.5)
    meanRV = ROOT.RooRealVar("mean", "mean", 2.5, 1.5, 3.5)
    argset = ROOT.RooArgSet(energyRV)
    data = ROOT.RooDataSet("data", "data", argset)
    c1 = ROOT.TCanvas()
    rooll = ROOT.RooLinkedList()
    for i in range(el.GetN()):
        main_tree.GetEntry(el.GetEntry(i))
        energyRV.setVal(-0.0125749*main_tree.energy)
        data.add(argset)
    gaussPeak = ROOT.RooGaussian("gauss", "gauss(energy, mean, sigma)", energyRV, meanRV, sigmaRV)
    gaussPeak.fitTo(data, ROOT.RooFit.FitOptions("Q"))
    xframe = energyRV.frame()
    data.plotOn(xframe, rooll)
    gaussPeak.plotOn(xframe)
    xframe.Draw()
    c1.Update()
    raw_input("TEMP")

    pd = run_doc.pulser_data
    pd.mean = meanRV.getVal() 
    pd.mean_err = meanRV.getError() 
    pd.sigma = sigmaRV.getVal() 
    pd.sigma_err = sigmaRV.getError() 
    return (run_doc, True)
