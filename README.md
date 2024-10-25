# FuelPrice Scraper
 
FuelPrice Scraper is a Python-based tool that scrapes fuel prices for various types of fuel such as Petrol, Diesel, and CNG across different states. This project leverages **Botasaurus** to automate the scraping and data retrieval process.
This script does not require any browser instance to scrap data and also bypass cloudflare and cookies protaction with request method.

## Setup

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/fuelprice-scraper.git
```
### 2. Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate   (for windows)
source venv/bin/activate  (for macOS/Linux)
```
### 3. Intsall dependencies 
```bash
pip install -r requirements.txt
```
### 4. Other Requirements
> Nodejs with global access
### 5. Start Project
```
python main.py
```
### 6. Curl Request
```
curl --location 'localhost:8000/all/<state_name>'
```

All State names are available in main.py file.



