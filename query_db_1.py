# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 17:42:14 2020

@author: MajidKhoshrou
"""

@ns.route('/target_emotion_metrics_ui2db/<search_term>, <platforms>', methods=['GET'])
@ns.doc(params={"search_term":"Enter a search terms, e.g., shimano", "platforms":"twitter, instagram, blogs, news or all"})

class query_db(Resource):
    
    """
    An easily configurable endpoint to access data from the sql database.
    Resource is an extrenal class!  search_term and platforms are two columns of the table in database.
    """

    def get(self, search_term, platforms): 

        server = config.insight_db_credentials['server'] 
        database = config.insight_db_credentials['database']
        username = config.insight_db_credentials['username']
        password = config.insight_db_credentials['password']
        driver=  config.insight_db_credentials['driver']
        cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

        cursor = cnxn.cursor()
        cursor.execute("SELECT * FROM [dbo].[table_name]")
        row = cursor.fetchall()
        available_platforms = list(list(row)[0])
        available_platforms.append('all')
        if platforms not in available_platforms:
            return f"Available platforms are: {available_platforms}", 400

        cursor = cnxn.cursor()
        cursor.execute("SELECT search_terms FROM [dbo].[table_name]")
        row = cursor.fetchall()
        available_search_terms = [ list(i)[0] for i in row ]
        if search_term not in available_search_terms:
            return "Bad request. Available search terms are: {}".format(available_search_terms), 400

        try:
            cursor = cnxn.cursor()
            cursor.execute(f"SELECT * FROM [dbo].[table_name] WHERE col_name = (?) AND col_name = (?) ", (search_term, platforms) )
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
 