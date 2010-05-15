from management.soudan_database import SoudanServer

server = SoudanServer()

# loop over all the accepted runs
for record in server.get_accepted_runs():
    doc = server.get_run(record.id)
    print "Run number: %s, gretina file: %s" %(doc._get_id(), doc.root_data_file_tier_1.pfn)
