def update_pulser_no_pulser_sets_for_rundoc(run_doc):
    """
      Updates a rundoc with the sets of events during a pulser
      and those not during a pulser 
    """
    import ROOT
    import os.path
    # first we check to see if we need to update
    if not os.path.exists(run_doc.output_data_file_tier_2.pfn):
        return (run_doc, False)
    last_event = 0
    for event in run_doc.pulser_off_set:
        if event[1] >= last_event: last_event = event[1]
    for event in run_doc.pulser_on_set:
        if event[1] >= last_event: last_event = event[1]

    open_file = ROOT.TFile(run_doc.output_data_file_tier_2.pfn)
    main_tree = open_file.Get("energy_output_tree") 
    if main_tree.GetEntries()-1 == last_event:
        return (run_doc, False)

    # we have to update
    no_pulser_set_list = []
    pulser_set_list = []
    eventlist = ROOT.TEventList("eventlist", "eventlist")

    main_tree.Draw(">>eventlist", "pulser_on")
    temp = [] 
    for i in range(eventlist.GetN()):
        if len(temp) == 0:
            temp.append(eventlist.GetEntry(i))
        elif eventlist.GetEntry(i) - eventlist.GetEntry(i-1) > 1: 
            temp.append(eventlist.GetEntry(i-1))
            pulser_set_list.append(temp)
            temp = [eventlist.GetEntry(i)]

    if len(temp) != 1 and eventlist.GetN() > 0:
        print "Error in pulser events: %s" % run_doc._get_id()
        return (run_doc, False)
    if len(temp) == 1:
        temp.append(eventlist.GetEntry(eventlist.GetN()-1))
        pulser_set_list.append(temp)

    main_tree.Draw(">>eventlist", "!pulser_on")
    temp = [] 
    for i in range(eventlist.GetN()):
        if len(temp) == 0:
            temp.append(eventlist.GetEntry(i))
        elif eventlist.GetEntry(i) - eventlist.GetEntry(i-1) > 1: 
            temp.append(eventlist.GetEntry(i-1))
            no_pulser_set_list.append(temp)
            temp = [eventlist.GetEntry(i)]

    if len(temp) != 1 and eventlist.GetN() > 0:
        print "Error in pulser events: %s" % run_doc._get_id()
        return (run_doc, False)
    if len(temp) == 1:
        temp.append(eventlist.GetEntry(eventlist.GetN()-1))
        no_pulser_set_list.append(temp)

    run_doc.pulser_on_set = pulser_set_list
    run_doc.pulser_off_set = no_pulser_set_list

    return (run_doc, True)

