import requests

class Review:
    def __init__(self):
        self.id = 0 # Generate Unique ID
        self.author = "" # UUID
        self.date = ""
        self.hours = 0
        self.content = ""
        self.comments = 0
        self.source = ""
        self.helpful = 0
        self.funny = 0
        self.recommend = True
        self.franchise = ""
        self.gameName = ""

def get_game_reviews(app_id):
    url = f"https://store.steampowered.com/appreviews/{app_id}?json=1"
    response = requests.get(url)
    review_data = response.json()
    url = f"http://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    game_data = response.json()
    
    if review_data['success'] and game_data[str(app_id)]['success']: # FIX: Allow app ids for games that dont exist to go through eg 0 & 100000000
        print(f"Reviews for the {game_data[str(app_id)]['data']['type']} '{game_data[str(app_id)]['data']['name']}' (App ID: {app_id}) have been saved.")
    else:
        return 'reviews not found'
        
print("Hello! Welcome to the Steam Review Crawler.")
print("Please enter the app ID for the game you wish to crawl.")
app_id = input("App ID: ")
while not app_id.isdigit():
    print("That is not a whole number. (eg. app id -> 1382330) Please try again")
    app_id = input("Enter app id: ")
get_game_reviews(app_id)