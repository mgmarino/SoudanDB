from ..views import view_virgin_start_of_run_time

def update_rundoc(run_doc):
    """
      Updates a rundoc with the local time of the start 
      Can be used to popluate a RunTimeDict
    """
    import datetime
    if run_doc.local_time_of_start_of_run:
        return (run_doc, False)
    string_to_parse = run_doc._get_id()
    datetime_obj = datetime.datetime(int(string_to_parse[0:4]),\
                                     int(string_to_parse[4:6]),\
                                     int(string_to_parse[6:8]),\
                                     int(string_to_parse[8:10]),\
                                     int(string_to_parse[10:12]),\
                                     int(string_to_parse[12:14]))
    run_doc.local_time_of_start_of_run = datetime_obj
    return (run_doc, True)

def get_view():
    return view_virgin_start_of_run_time.get_view_class()
