import json
import requests
import urllib.parse
import datetime
import uuid
import hashlib
import os
from dateutil.parser import parse

#
class Review:
    def __init__(self, author, date, hours, content, comments, source, helpful, funny, recommend, franchise, gameName):
        self.id = self.generate_id(gameName, content, author) # Unique reproducible review ID
        self.author = str(uuid.uuid5(uuid.NAMESPACE_DNS, author)) # UUID of author steam ID
        self.date = date # 
        self.hours = hours #
        self.content = content #
        self.comments = comments #
        self.source = source #
        self.helpful = helpful #
        self.funny = funny #
        self.recommend = recommend #
        self.franchise = franchise #
        self.gameName = gameName #
        
    def generate_id(self, gameName, content, author):
        # Combine review fields and normalise
        id_string = f"{gameName}-{content}-{author}".lower()
        # Convert to UTF-8
        encoded_id = id_string.encode('utf-8')
        # Apply SHA-256 hashing
        hash_object = hashlib.sha256(encoded_id)
        hex_digest = hash_object.hexdigest()
        return hex_digest

# Crawls the apps steam site to fetch reviews and app information
def fetch_app_data(app_id, date_filters):
    found = 0; reviews = []; cursor = "*"; print("\nFetching Reviews... (this may take a few seconds)")
    if date_filters == [None, None]:
        for i in range(50):
            url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100&filter=recent&cursor={cursor}"
            response = requests.get(url)
            review_data = response.json()
            cursor = urllib.parse.quote_plus(review_data["cursor"])
            reviews.append(review_data)
            found = found + len(review_data["reviews"])
        else:
            print()
    else:
        days_ago = (datetime.date.today() - datetime.date.fromisoformat(date_filters[0])).days; print(days_ago)
        #
        for i in range(50):
            url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100&filter=all&cursor={cursor}&day_range={days_ago}"
            response = requests.get(url)
            review_data = response.json()
            cursor = urllib.parse.quote_plus(review_data["cursor"])
            reviews.append(review_data)
            found = found + len(review_data["reviews"])
    
    print("Fetching App Info...")
    url = f"http://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    game_data = response.json()
    
    if review_data['success'] and game_data[str(app_id)]['success']: # FIX: Allow app ids for games that dont exist to go through eg 0 & 100000000
        data = [reviews, game_data]
        print(f"Fetched {found} reviews and app info")
        return data 
    else:
        return 'reviews not found'

# 
def organise_reviews(reviews_array, game_data):
    review_list = []
    for i in range(len(reviews_array)):
        review_data = reviews_array[i]["reviews"]
        for i in range(len(review_data)):
            review = Review(
                author=review_data[i]["author"]["steamid"],
                date=datetime.datetime.fromtimestamp(review_data[i]["timestamp_created"]).strftime("%Y-%m-%d"),
                hours=review_data[i]["author"]["playtime_at_review"],
                content=review_data[i]["review"],
                comments=review_data[i]["comment_count"],
                source="steam",
                helpful=review_data[i]["votes_up"],
                funny=review_data[i]["votes_funny"],
                recommend=review_data[i]["voted_up"],
                franchise=game_data[str(app_id)]["data"]["developers"],
                gameName=game_data[str(app_id)]["data"]["name"]
                )
            review_dict = review.__dict__
            review_list.append(review_dict)
    # Sort list of reviews by date then by id
    sorted_reviews = sorted(review_list, key=lambda x: (x["date"], x["id"]))
    return sorted_reviews


# Main section 
print("\nHello! Welcome to the Steam Review Crawler.")
print("\nPlease enter the app ID for the game you wish to crawl.")
app_id = input("App ID: ")

# Check input and TODO if app exists
while not app_id.isdigit():
    print("That is not a whole number. (eg. 1382330) Please try again")
    app_id = input("Enter app id: ")

filter = None; date_filters = [None, None]
while True:
    print("\nWould you like to filter the reviews between two dates? (y/yes or n/no)")    
    filter = input("Enter:")
    if filter.lower() == "y" or filter.lower() == "yes":
        while True:
            print("\nPlease enter the start date for the filter. Cannot be more than 1 year ago. (format 2024-12-31)")
            date_filters[0] = (input("Enter:"))
            try:
                dateobj = datetime.date.fromisoformat(date_filters[0])
            except ValueError:
                print("That is not a valid response. Please try again.")
            except:
                print("Something went wrong. Maybe you set the date to the future.")
            else:
                if dateobj <= datetime.date.today(): # TODO: Stop it from going past 365 days ago
                    break
                else:
                    print("Date cannot be in the future.")
        while True:
            print("\nPlease enter the end date for the filter. (format 2024-12-31)")
            date_filters[1] = (input("Enter:"))
            try:
                dateobj = datetime.date.fromisoformat(date_filters[1])
            except ValueError:
                print("That is not a valid response. Please try again.")
            except:
                print("Something went wrong. Maybe you set the date to the future.")
            else:
                if dateobj <= datetime.date.today():
                    break
                else:
                    print("Date cannot be in the future.")
        break
    elif filter.lower() == "n" or filter.lower() == "no":
        filter = None
        break
    else:
        print("That is not a valid response. Please try again")

# Fetch App and Review 
app_data = fetch_app_data(app_id, date_filters)
review_array = organise_reviews(app_data[0], app_data[1])

print("\nSaving data to " + f'./reviews/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{str(app_id)}_Reviews.json')
cur_path = os.path.dirname(__file__)
# Dynamic name file in format of 'Year-Month-Day_Hour-Minutes-Seconds_AppID_Reviews.json'
new_path = os.path.relpath(f'.\\reviews\\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{str(app_id)}_Reviews.json', cur_path)
with open(new_path, 'w') as f:
    json.dump(review_array, f, indent=4)
print(f"Reviews for the {app_data[1][str(app_id)]['data']['type']} '{app_data[1][str(app_id)]['data']['name']}' (App ID: {app_id}) have been saved.")