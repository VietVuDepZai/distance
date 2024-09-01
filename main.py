from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
import math
import uvicorn

app = FastAPI()

# Function to geocode an address
def geocode(address: str):
    geocode_url = 'https://geocode.search.hereapi.com/v1/geocode'
    params = {
        'q': address,
        'apiKey': 'FKJdByW7d_QmFSdN8y8dF2f4x7pVNMHtgXb8O7Yr3So'  # Replace with your API key
    }
    response = requests.get(geocode_url, params=params)
    response.raise_for_status()
    data = response.json()
    if data['items']:
        return data['items'][0]['position']['lat'], data['items'][0]['position']['lng']
    else:
        return None  # Return None if no results found

# Function to calculate the Haversine distance
def haversine(lat1: float, lon1: float, lat2: float, lon2: float):
    R = 6371  # Radius of the Earth in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Distance in km

@app.get("/distance")
async def get_distance(
    address1: str = Query('', description="First address"),
    address2: str = Query('', description="Second address"),
    transport_mode: str = Query('car', description="Transport mode (car, bike, etc.)")
):
    # Geocode the addresses
    coords1 = geocode(address1)
    coords2 = geocode(address2)

    # Check if geocoding was successful
    if not coords1 or not coords2:
        raise HTTPException(status_code=400, detail="Geocoding failed for one or both addresses.")

    # Calculate the Haversine distance
    distance = haversine(coords1[0], coords1[1], coords2[0], coords2[1])

    # If the distance is greater than 4.5 km, return a response indicating the route exceeds the allowed distance
    if distance > 4.5:
        raise HTTPException(status_code=500, detail="The distance is too far.")

    # Construct the HERE API URL
    url = 'https://router.hereapi.com/v8/routes'
    params = {
        'transportMode': transport_mode,
        'origin': f"{coords1[0]},{coords1[1]}",
        'destination': f"{coords2[0]},{coords2[1]}",
        'return': 'summary',
        'apiKey': 'FKJdByW7d_QmFSdN8y8dF2f4x7pVNMHtgXb8O7Yr3So'  # Replace with your API key
    }

    try:
        # Make the request to the HERE API
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()  # Parse the JSON response

        # Extract the summary information
        route = data.get('routes', [{}])[0]  # Get the first route
        summary = route.get('sections', [{}])[0].get('summary', {})  # Get the summary of the first section

        # Return the summary as JSON
        return JSONResponse(content=summary)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/")
def home():
    return {"data": "Hello World"}
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
