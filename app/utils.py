import configparser
import os, sys, glob
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import operator
import gc
from IPython.display import HTML

config = configparser.ConfigParser()
config.read(os.path.expanduser('~/db_config.ini'))

def db_connection(database_name='DB'):
    conn = psycopg2.connect(
            database=config[database_name]['DATABASE'],
            host=config[database_name]['HOST'],
            port=config[database_name]['PORT'],
            user=config[database_name]['USERNAME'],
            password=config[database_name]['PASSWORD']
      )
    return conn
    
def dataframe_from_sql_query(connection, sql_query):
    cursor = connection.cursor()
    cursor.execute(sql_query)
    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return pd.DataFrame(list(rows), columns=column_names)


hide_cell = '''<script>
code_show=true; 
function code_toggle() {
    if (code_show){
        $('div.cell.code_cell.rendered.selected div.input').hide();
    } else {
        $('div.cell.code_cell.rendered.selected div.input').show();
    }
    code_show = !code_show
} 

$( document ).ready(code_toggle);
</script>

To show/hide this cell's raw code input, click <a href="javascript:code_toggle()">here</a>.'''

hide_all = '''
<script>
    code_show=true; 
    function code_toggle() {
     if (code_show){
     $('div.input').hide();
     } else {
     $('div.input').show();
     }
     code_show = !code_show
    } 
    $( document ).ready(code_toggle);
</script>
<form action="javascript:code_toggle()">
    <input type="submit" value="Click here to toggle on/off the raw code.">
</form>'''