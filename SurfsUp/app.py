# Import the dependencies.

from flask import Flask, jsonify
import datetime as dt
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

#################################################
# Database Setup
#################################################


# reflect an existing database into a new model

# reflect the tables

engine = create_engine("sqlite:///hawaii.sqlite") 
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table


# Create our session (link) from Python to the DB

Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last 12 months."""
    session = Session(engine)
    
    # Query for the last 12 months of precipitation data
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    year_ago = last_date - dt.timedelta(days=365)
    
    precipitation_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_ago).all()
    session.close()

    # Convert the query results to a dictionary using `date` as the key and `prcp` as the value
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    session = Session(engine)
    
    # Query all stations
    results = session.query(Station.station).all()
    session.close()

    # Unravel results into a 1D array and convert to a list
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return the temperature observations for the previous year for the most active station."""
    session = Session(engine)
    
    # Find the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]
    
    # Query the temperature observations for the last year
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    year_ago = last_date - dt.timedelta(days=365)
    
    tobs_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= year_ago).all()
    
    session.close()

    # Convert to a list of dictionaries
    tobs_list = list(np.ravel(tobs_data))

    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def stats(start=None, end=None):
    """Return TMIN, TAVG, TMAX for a specified start or start-end range."""
    session = Session(engine)

    if not end:
        # Calculate TMIN, TAVG, TMAX for dates >= start
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()
    else:
        # Calculate TMIN, TAVG, TMAX for dates between start and end
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).\
            filter(Measurement.date <= end).all()

    session.close()

    # Convert to a list
    temp_stats = list(np.ravel(results))

    return jsonify(temp_stats)

if __name__ == '__main__':
    app.run(debug=True)