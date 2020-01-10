from app import app
from app.forms import ClaimForm
from flask import render_template, flash, redirect, url_for, request
from app.claim_telematics import TripTable, get_trip_list, plot_trips
from flask_table import Table, Col, LinkCol, ButtonCol
from collections import deque
import os, sys

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():


    # Declare your table
    # class ItemTable(Table):
    #    name = Col('name')
    #    description = LinkCol('description', endpoint='index')

    # items = [dict(name='Name1', description='Description1'),
    #         dict(name='Name2', description='Description2'),
    #         dict(name='Name3', description='Description3')]

    # table = ItemTable(items)
    # return table.__html__()

    form = ClaimForm()
    if form.validate_on_submit():
        claim_number = form.claim_num.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        #interested_trips = get_trip_list(claim_number, start_date, end_date)
        
        #if not interested_trips:
        #    return "no trip found"

        #plot_trips(interested_trips, claim_number)

        #return redirect(url_for('.claim_result', claim_number=claim_number))
        
        return redirect(url_for('result', claim_number=claim_number, start_date=start_date, end_date=end_date))
    return render_template('index.html', title='Claim Telematics', form=form)

#@app.route('/result/<claim_number>')
#def claim_result(claim_number):
#    return render_template('result.html', title=claim_number)
#    #return render_template('result.html', title=claim_number, tables=[request.args.get('trips')])
    
    
results = dict()
    
@app.route('/result')
def result():
    claim_number = request.args.get('claim_number')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not claim_number in results:
        trips = get_trip_list(claim_number)
        results[claim_number] = trips
        
    if results[claim_number] is None:
        return render_template('error.html', message="No trip found for user")
    
    return render_template('result.html', claim_number=claim_number, start_date=start_date, end_date=end_date)
    #return redirect(url_for('trip_table', claim_number=claim_number, start_date=start_date, end_date=end_date))
    #return render_template('result.html', title=claim_number)
    #return render_template('result.html', title=claim_number, tables=[request.args.get('trips')])
 
@app.route('/trip_table')
def trip_table():
    claim_number = request.args.get('claim_number')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not claim_number in results:
        trips = get_trip_list(claim_number)
        results[claim_number] = trips
        
    trips = results[claim_number]
    interested_trips = trips.loc[trips.start_time_local >= start_date].loc[trips.start_time_local <= end_date]
    if len(interested_trips)==0:
        return render_template('error.html', message="no trip found in time frame")

    d = interested_trips.to_dict(orient='record')
    table = TripTable(d)
    table.border = True
    table.html_attrs = {'cellpadding': 2}
    return table.__html__()

@app.route('/trip_map')
def trip_map():
    claim_number = request.args.get('claim_number')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    trip = request.args.get('trip')
    location = (request.args.get('lat'), request.args.get('long'))
    
    if claim_number and start_date and end_date:
        if not claim_number in results:
            trips = get_trip_list(claim_number)
            results[claim_number] = trips
        
        trips = results[claim_number]
        interested_trips = trips.loc[trips.start_time_local >= start_date].loc[trips.start_time_local <= end_date]
        trip_files = list(interested_trips.data_file_name)
        filename = 'maps/'+claim_number+start_date.replace('-','')+end_date.replace('-','')+'.html'
        
    elif trip:
        trip_files = list(trip)
        filename = trip[:-4]+'.html'
        
    else:
        return render_template('error.html', message="invalid request for map")
        
    if len(trip_files)>100:
        return render_template('error.html', message="too many trips to plot, can you refine the time frame?")
    
    #print(claim_number, start_date, end_date)
    #print(trip_files)
    if not os.path.isfile(filename):
        message = plot_trips(trip_files, None, filename)
        if message != "done":
            return render_template('error.html', message="error plotting map (probably no trip had GPS)")
        
    file = open(filename, "r")
    return file.read()
    

@app.route('/blog')
def blog():
    user = {'username': 'root'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('blog.html', title='Home', user=user, posts=posts)
