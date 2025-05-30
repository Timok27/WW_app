from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import pandas as pd
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_coordinates(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "ru", "format": "json"}
    response = requests.get(url, params=params).json()
    if not response.get("results"):
        return None
    location = response["results"][0]
    return location["latitude"], location["longitude"]


def get_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation,precipitation_probability,relative_humidity_2m",
        "forecast_days": 1,
        "timezone": "auto"
    }
    response = requests.get(url, params=params).json()
    hourly = response.get("hourly", {})
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    df = df.head(12)  
    return df


@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
async def forecast(request: Request, city: str = Form(...)):
    coords = get_coordinates(city)
    if not coords:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Город не найден"})
    df = get_weather(*coords)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "city": city,
        "weather_data": df.to_dict(orient="records")
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)