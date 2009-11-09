import management.soudan_database 

def insert_view_into_database(view):
    """
    Function inserts a view into the database.
    Type of view should be an couchdb.schema.ViewDefinition 
    """
    
    server = management.soudan_database.SoudanServer()
    view.sync(server.get_database())
