from ..views import view_virgin_runstart_time
import ROOT, plistlib
import dateutil.parser as parse

def update_rundoc(rundoc):
    """
    Returns whether or not the rundoc has been updated.
    """
    if rundoc.local_time_of_start_of_run:
        return (rundoc, False)
    open_file = ROOT.TFile(rundoc.root_data_file_tier_1.pfn)
    header_xml = open_file.Get("headerXML") 
    obj = plistlib.readPlistFromString(header_xml.String().Data())
    rundoc.local_time_of_start_of_run = parse.parse(obj['Document Info']['date'])
    return (rundoc, True)

def get_view():
    return view_virgin_runstart_time.get_view_class()
