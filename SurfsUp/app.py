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

measurement = Base.classes.get('measurement')
Station = Base.classes.get('station')

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

    # Query for the last date in the Measurement table
    last_date_row = session.query(measurement.date).order_by(measurement.date.desc()).first()

    # Print the result of the query for debugging
    print(f"Last date query result: {last_date_row}")

    if last_date_row:
        # Unpack the first element of the tuple
        last_date = last_date_row[0]
        last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
        year_ago = last_date - dt.timedelta(days=365)
    else:
        # If no data is found, return an appropriate message
        return jsonify({"error": "No data found for dates"}), 404

    # Query precipitation data for the last 12 months
    precipitation_data = session.query(measurement.date, measurement.prcp).filter(measurement.date >= year_ago).all()
    session.close()

    # Handle empty query result
    if not precipitation_data:
        return jsonify({"error": "No precipitation data available"}), 404

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
    most_active_station = session.query(measurement.station, func.count(measurement.station)).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).first()[0]
    
    # Query the temperature observations for the last year
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    year_ago = last_date - dt.timedelta(days=365)
    
    tobs_data = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == most_active_station).\
        filter(measurement.date >= year_ago).all()
    
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
        results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).all()
    else:
        # Calculate TMIN, TAVG, TMAX for dates between start and end
        results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).\
            filter(measurement.date <= end).all()

    session.close()

    # Convert to a list
    temp_stats = list(np.ravel(results))

    return jsonify(temp_stats)

if __name__ == '__main__':
    app.run(debug=True)