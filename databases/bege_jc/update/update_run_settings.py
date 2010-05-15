from ..views import view_virgin_settings_docs
def update_rundoc(run_doc):
    """
      Updates a rundoc with the settings stored 
      in the settings file
    """
    import os.path
    if not os.path.exists(run_doc.settings_data_file.pfn):
        return (run_doc, False)
    elif len(run_doc.run_settings) != 0:
        return (run_doc, False)
    open_file = open(run_doc.settings_data_file.pfn, 'r')
    temp = []
    while 1:
        temp_str = open_file.readline() 
        if not temp_str: break
        temp.append(temp_str.strip())
    run_doc.run_settings = temp
    return (run_doc, True)

def get_view():
    return view_virgin_settings_docs.get_view_class()
