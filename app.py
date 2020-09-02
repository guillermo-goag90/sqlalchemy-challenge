from flask import Flask, request, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

# Create classes
Measurement = Base.classes.measurement
Station = Base.classes.station

# Calculate last twelve months start date
session = Session(engine)
end_date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
session.close()

end_date = str(end_date_query[0])
date_pieces = end_date.split('-')

# Change year to include last twelve months of data
start_year = str(int(date_pieces[0]) - 1)

# Create new date string (text format)
ltm_start_date = f'{start_year}-{date_pieces[1]}-{date_pieces[2]}'

# input arbitrary start and end date
input_start_date = '2013-05-20'
input_end_date = '2017-05-20'

# Init app
app = Flask(__name__) 

@app.route("/")
def welcome():
    """List all available api routes."""
   
    return (
        'Welcome to Climate, an API-based web app. Explore the following:<br/>'
        '<br/>'
        f'api/v1.0/precipitation<br/>'
        f'api/v1.0/stations<br/>'
        f'api/v1.0/tobs<br/>'
        f'/api/v1.0/<start><br/>'
        f'/api/v1.0/<start>/<end>'
    )

@app.route('/v1.0/precipitation')
def prcp():
    """Returns precipitation data based on a start date."""

    session = Session(engine)
    prcp = session.query(Measurement.date, Measurement.prcp).\
                filter(Measurement.date >= ltm_start_date).\
                    order_by(Measurement.date.asc()).\
                        all()
    session.close()

    #prcp_dict ={'precipitation_data': dict(prcp)}
    prcp_obs_by_date = {}
    for date, prcp in prcp:
        prcp_obs_by_date.setdefault(date, []).append(prcp)
    
    prcp_dict = {'precipitation': prcp_obs_by_date}
    return jsonify(prcp_dict)

@app.route('/v1.0/stations')
def stations():
    """Returns a JSON list of stations from the dataset."""

    session = Session(engine)
    stations = session.query(Station.station)
    session.close()
    
    station_dict = {'stations': [station[0] for station in stations]}
    return jsonify(station_dict)

@app.route('/v1.0/tobs')
def tobs():
    """Return a JSON list of temperature observations (TOBS) for the previous year."""

    session = Session(engine)
    station_act = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).\
                all()
    
    top_station = station_act[0][0]

    top_station_tobs = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == top_station).\
            filter(Measurement.date >= ltm_start_date).\
                all()
    
    session.close()

    top_station_tobs_dict = {'temp_obs_for_top_station': [dict(top_station_tobs)]}
    return jsonify(top_station_tobs_dict)

@app.route('/v1.0/<start>')
@app.route('/v1.0/<start>/<end>')
def temp_start(start=input_start_date, end=input_end_date):
    """Return a JSON list of the minimum temperature, the average temperature, 
        and the max temperature for a given start or start-end range."""

    session = Session(engine)

    if end == None:
        temps = session.query(func.min(Measurement.tobs), 
                                func.avg(Measurement.tobs), 
                                func.max(Measurement.tobs)).\
                                    filter(Measurement.date >= start).\
                                        all()
    else:
        temps = session.query(func.min(Measurement.tobs), 
                                func.avg(Measurement.tobs), 
                                func.max(Measurement.tobs)).\
                                    filter(Measurement.date >= start).\
                                        filter(Measurement.date <= end).\
                                        all()

    session.close()

    keys = ['TMIN', 'TAVG', 'TMAX']
    temps = list(temps[0])
    dates_temp_dict = zip(keys, temps)
    min_max_dict = dict(dates_temp_dict)

    return jsonify(min_max_dict)


# Run Server (check to see if this is the main file)
if __name__ == "__main__":
    app.run(debug=True)