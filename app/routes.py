from app import app
from app.forms import ClaimForm
from flask import render_template, flash, redirect, url_for, request
from app.claim_telematics import get_trip_list, plot_trips

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = ClaimForm()
    if form.validate_on_submit():
        claim_number = form.claim_num.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        interested_trips = get_trip_list(claim_number, start_date, end_date)
        #return redirect(url_for('index'))
        #return render_template('result.html', title=str(claim_number), tables=[interested_trips.to_html(classes='data', header="true")])
        #return claim_result(claim_number, interested_trips)
        #return redirect(url_for('.claim_result', claim_number=str(claim_number), trips=interested_trips))
        trip_map = plot_trips(interested_trips)
        trip_map.save('templates/map.html')
        return redirect(url_for('.claim_result', claim_number=claim_number, trips=interested_trips.to_html(classes='data', header="true")))
    return render_template('index.html', title='Claim Telematics', form=form)

@app.route('/result/<claim_number>')
def claim_result(claim_number):
    #return render_template('result.html', title=str(claim_number), tables=[trips.to_html(classes='data', header="true")])
    return render_template('result.html', title=claim_number, tables=[request.args.get('trips')])


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
