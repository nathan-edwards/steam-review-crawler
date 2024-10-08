# Steam Review Crawler

This Python script crawls Steam app reviews and saves them to JSON files.

## Features

- Fetches reviews for a specified Steam app ID.
- Allows filtering reviews by date range.
- Option to fetch all reviews possible or a specific number of pages (1 page = 100 reviews).
- Organizes reviews into `Review` objects with relevant information (author, date, hours played, content, etc.).
- Saves reviews to JSON files (one file per 5000 reviews).

## Requirements

- Python 3.7 or higher
- `requests` library
- `dateutil` library

## Installation

**Clone the repository:**
   
```
git clone https://github.com/nathan-edwards/steam-review-crawler
```

**Install dependencies:**
```
pip install .\requirements.txt
```

**Run the crawler**
```
python .\main.py
```

**Test the crawler**
```
python -m unittest .\test.py
```