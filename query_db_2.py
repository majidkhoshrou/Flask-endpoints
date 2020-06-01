# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 17:45:45 2020

@author: MajidKhoshrou
"""


@ns.route('/name of endpoint/<input argument>', methods=['GET'])
@ns.doc(params={"search_term":"Enter a search term, e.g., shimano"})
class query_db_2(Resource):
    
    """
    An endpoint to access data from database. 
    For more info see https://docs.microsoft.com/en-us/sql/connect/python/pyodbc/step-3-proof-of-concept-connecting-to-sql-using-pyodbc?view=sql-server-ver15

    """

    def get(self, search_term): 
        server = config.insight_db_credentials['server'] 
        database = config.insight_db_credentials['database']
        username = config.insight_db_credentials['username']
        password = config.insight_db_credentials['password']
        driver=  config.insight_db_credentials['driver']
        cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

        cursor = cnxn.cursor()
        cursor.execute("SELECT col_name FROM [dbo].[table_name]")
        row = cursor.fetchall()
        available_search_terms = [ list(i)[0] for i in row ]
        if search_term not in available_search_terms:
            return "Bad request. Available search terms are: {}".format(available_search_terms), 400

        try:
            cursor = cnxn.cursor()
            cursor.execute("SELECT * FROM [dbo].[table_name] WHERE search_terms = (?)", (search_term) )
            num_fields = len(cursor.description)
            field_names = [i[0] for i in cursor.description]
            row = cursor.fetchall()
            vals = [str(i) for i in row[0]]
            output = json.dumps(dict(zip(field_names,vals)))
            return json.loads(output)
        except Exception as e:
            print(type(e))
            template = " An exception of type < {0} > occurred ==> Arguments: {1!r}"
            message = template.format(type(e).__name__, e.args)
            (logging.error(message))
            return ""
 