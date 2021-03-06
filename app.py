from flask import Flask, flash, render_template, request, redirect, url_for
from wtforms import Form, StringField, BooleanField
import requests
import pandas as pd
import re #reg expressions
from bokeh.plotting import figure
from bokeh.palettes import Spectral4 #color palette for line plots
from bokeh.embed import components #to generate embedded html


def get_stock_data(stock):
    # get quandl data for stock ticker stock
    api_url = 'https://www.quandl.com/api/v1/datasets/WIKI/%s.json' % stock
    session = requests.Session()
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    raw_data = session.get(api_url)
    return raw_data.json()    

def make_dataframe(json_data):
    # make pandas dataframe from json_data
    df = pd.DataFrame(json_data['data'],columns=json_data['column_names'])
    df = df.set_index('Date')
    df.index = pd.to_datetime(df.index)
    return df    

class UIForm(Form):
    # makes a form for grabbing user input
    stock = StringField('Ticker symbol')
    Closing = BooleanField('Closing price')
    Opening = BooleanField('Opening price')
    Adj_closing = BooleanField('Adjusted closing price')
    Adj_opening = BooleanField('Adjusted opening price')


app = Flask(__name__)
app.secret_key = '\xb6\xbcr\xc4\xb5\x9cY\x03\xcdI\x15oR:\xdbJD\xb1c\x00+\x1c\x926'

@app.route('/') #redirect to index page
def main():
  return redirect('/index')

# page where user selects desired stock features to plot
@app.route('/index',methods=['GET','POST'])
def index():
    form =  UIForm(request.form)
    if request.method == 'POST':  #if user is posting, get form data and store it  
        app.UIform = form
        if not form.stock.data: #if the stock string field is empty, redirect to form page
            flash('Need to input a valid tock ticker')
            return redirect('/index')
        json_data = get_stock_data(app.UIform.data['stock']) #try getting data from quandl
        app.json_data = json_data #store json data
        if 'error' in json_data: #if the request from quandl failed, redirect and flash error
            flash('Need to input a valid tock ticker')
            return redirect('/index')
        return redirect('/graph') #otherwise, go to the graph page
    return render_template('index.html',form=form) #if request method was GET
    
#page for displaying the requested graph
@app.route('/graph')
def graph():
    company_name, = re.match(r'(.+) \({}\)'.format(app.UIform.data['stock']),
                             app.json_data['name']).groups() #get company name for plotting
    df = make_dataframe(app.json_data) #make a pandas dataframe
    name_map = { #maps form field names to names of columns in dataframe
                'Closing':'Close',
                'Opening':'Open',
                'Adj_closing':'Adj. Close',
                'Adj_opening':'Adj. Open'}
    #get set of dataframe columns the user wants to plot
    plot_set = [name_map[key] for key in app.UIform.data.keys() if app.UIform.data[key] == True]
                
    #make a color palette for the lines
    numlines=len(plot_set) 
    mypalette=Spectral4[0:numlines]
    
    plot = figure(width=800, height=600, x_axis_type="datetime",title=company_name) #make plot
    #add individual lines
    for indx,line_name in enumerate(plot_set):
        plot.line(df.index,
                  df[line_name],
                  line_color=mypalette[indx],
                  line_width=2,
                  legend=line_name)

    script, div = components(plot) #make html components

    return render_template('graph.html', stock_name = company_name, script=script, div=div)


if __name__ == '__main__':
  app.run(port=33507)
    