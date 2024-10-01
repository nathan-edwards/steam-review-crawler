import uuid
import hashlib
import requests
import urllib.parse
from datetime import datetime
import json

class Review:
    
    def __init__(self, author, date, hours, content, comments, source, helpful, funny, recommend, franchise, gameName):
        self.id = self.generate_id(gameName, content, author) # Generate Unique ID
        self.author = str(uuid.uuid5(uuid.NAMESPACE_DNS, author)) # UUID
        self.date = date
        self.hours = hours
        self.content = content
        self.comments = comments
        self.source = source
        self.helpful = helpful
        self.funny = funny
        self.recommend = recommend
        self.franchise = franchise
        self.gameName = gameName
        
    def generate_id(self, gameName, content, author):
        # Combine review fields and normalise
        id_string = f"{gameName}-{content}-{author}".lower()
        # Convert to UTF-8
        encoded_id = id_string.encode('utf-8')
        # Apply SHA-256 hashing
        hash_object = hashlib.sha256(encoded_id)
        hex_digest = hash_object.hexdigest()
        return hex_digest

def get_app_data(app_id):
    found = 0
    reviews = []
    cursor = "*"
    print("Requesting Reviews...")
    for i in range(50):
        url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100&filter=recent&cursor={cursor}"
        response = requests.get(url)
        review_data = response.json()
        cursor = urllib.parse.quote_plus(review_data["cursor"])
        reviews.append(review_data)
        found = found + len(review_data["reviews"])
    
    print("Requesting Game Info...")
    url = f"http://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    game_data = response.json()
    
    if review_data['success'] and game_data[str(app_id)]['success']: # FIX: Allow app ids for games that dont exist to go through eg 0 & 100000000
        data = [reviews, game_data]
        print(f"Received Game Info & {found} Reviews")
        return data 
    else:
        return 'reviews not found'

def extract_reviews(reviews_array, game_data):
    review_array = []
    for i in range(len(reviews_array)):
        review_data = reviews_array[i]["reviews"]
        for i in range(len(review_data)):
            review = Review(
                author=review_data[i]["author"]["steamid"],
                date=str(datetime.fromtimestamp(review_data[i]["timestamp_created"])),
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
            review_array.append(review_dict)
    return review_array
        
print("Hello! Welcome to the Steam Review Crawler.")
print("Please enter the app ID for the game you wish to crawl.")
app_id = input("App ID: ")
while not app_id.isdigit():
    print("That is not a whole number. (eg. 1382330) Please try again")
    app_id = input("Enter app id: ")
app_data = get_app_data(app_id)
review_array = extract_reviews(app_data[0], app_data[1])

with open('reviews.json', 'w') as f: # TODO: make the file name dynamic
    json.dump(review_array, f, indent=4)
print(f"Reviews for the {app_data[1][str(app_id)]['data']['type']} '{app_data[1][str(app_id)]['data']['name']}' (App ID: {app_id}) have been saved.")