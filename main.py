import datetime
import hashlib
import json
import requests
import urllib.parse
import uuid
import os
from dateutil.parser import parse
from itertools import count
from pathlib import Path


class Review:
    def __init__(
        self,
        author,
        date,
        hours,
        content,
        comments,
        source,
        helpful,
        funny,
        recommend,
        franchise,
        appName,
    ):
        """
        Initializes a Review object.

        Args:
            author (str): The author's Steam ID.
            date (str): The date of the review (YYYY-MM-DD format).
            hours (int): The number of hours the author has played the game/app.
            content (str): The review text.
            comments (int): The number of comments on the review.
            source (str): The source of the review (e.g., "steam").
            helpful (int): The number of users who found the review helpful.
            funny (int): The number of users who found the review funny.
            recommend (bool): Whether the author recommends the game/app.
            franchise (str): The name of the game/app's developer.
            appName (str): The name of the game/app.
        """
        self.id = self.generate_id(appName, content, author)
        self.author = str(uuid.uuid5(uuid.NAMESPACE_DNS, author))
        self.date = date
        self.hours = hours
        self.content = content
        self.comments = comments
        self.helpful = helpful
        self.funny = funny
        self.recommend = recommend
        self.franchise = franchise
        self.appName = appName

    def generate_id(self, appName, content, author):
        """
        Generates a unique ID for the review.

        Args:
            appName (str): The name of the game/app.
            content (str): The review text.
            author (str): The author's Steam ID.

        Returns:
            str: The unique review ID.
        """
        # Combine review fields and normalise
        id_string = f"{appName}-{content}-{author}".lower()
        encoded_id = id_string.encode("utf-8")
        # Apply SHA-256 hashing
        hash_object = hashlib.sha256(encoded_id)
        hex_digest = hash_object.hexdigest()
        return hex_digest


# TODO integrate number of reviews
def fetch_app_data(app_id, date_filters, numReviews):
    """
    Fetches reviews and app information from Steam.

    Args:
        app_id (int): The Steam app ID.
        date_filters (list): A list of two date strings (YYYY-MM-DD format)
            to filter reviews by date range.
        numReviews (int): The number of reviews to fetch.

    Returns:
        tuple: A tuple containing a list of reviews and a dictionary of app information.
    """
    found = 0  # Keeps track of how many reviews are found
    reviews = []  # List to store review data
    cursor = "*"  # Cursor to paginate through the Steam API's review pages

    # Fetch reviews
    print("\nFetching Reviews... (this may take a while)")
    if numReviews == 0:
        for i in count(0):
            url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100&filter=recent&cursor={cursor}"
            response = requests.get(url)
            review_data = response.json()
            # Stop fetching if no more reviews are available
            if review_data["query_summary"]["num_reviews"] == 0:
                break
            cursor = urllib.parse.quote_plus(review_data["cursor"].encode())
            reviews.append(review_data)
            found = found + len(review_data["reviews"])
            print(f"Found {found} so far...", end="\r")
        else:
            print("Error")
    else:
        for i in range(numReviews):
            url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100&filter=recent&cursor={cursor}"
            response = requests.get(url)
            review_data = response.json()
            # Stop fetching if no more reviews are available
            if review_data["query_summary"]["num_reviews"] == 0:
                break
            cursor = urllib.parse.quote_plus(review_data["cursor"].encode())
            reviews.append(review_data)
            found = found + len(review_data["reviews"])
            print(f"Found {found} so far...", end="\r")
        else:
            print("Error")

    # Fetch info
    print("Fetching App Info...")
    url = f"http://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    game_data = response.json()

    if "success" in review_data and review_data["success"] and "success" in game_data[str(app_id)] and game_data[str(app_id)]["success"]:
        data = (reviews, game_data)  # Return as a tuple
        print(f"Fetched {found} reviews and app info")
        return data
    else:
        return "reviews not found" 


def organise_reviews(reviews_array, game_data, date_filters, app_id):
    """
    Organizes the fetched reviews into Review objects and sorts them.

    Args:
        reviews_array (list): A list of dictionaries containing review data.
        game_data (dict): A dictionary containing app information.
        date_filters (list): A list of two date strings (YYYY-MM-DD format)
            to filter reviews by date range.

    Returns:
        list: A list of lists, where each inner list contains Review objects for a single page.
    """
    review_list = [[]]  # List of lists to store reviews, divided into pages
    counter = 0  # Counter to track the number of reviews per page
    pageNum = 0  # Page number tracker
    print("\nConverting Reviews into Objects...")

    # Process reviews when no date filter is applied
    if date_filters == [None, None]:
        for i in range(len(reviews_array)):
            review_data = reviews_array[i]["reviews"]
            for i in range(len(review_data)):
                if counter == 5000:
                    review_list.append([])
                    pageNum += 1
                    counter = 0
                review_dict = Review(
                    author=review_data[i]["author"]["steamid"],
                    date=datetime.datetime.fromtimestamp(
                        review_data[i]["timestamp_created"]
                    ).strftime("%Y-%m-%d"),
                    hours=review_data[i]["author"]["playtime_at_review"],
                    content=review_data[i]["review"],
                    comments=review_data[i]["comment_count"],
                    source="steam",
                    helpful=review_data[i]["votes_up"],
                    funny=review_data[i]["votes_funny"],
                    recommend=review_data[i]["voted_up"],
                    franchise=game_data[str(app_id)]["data"]["developers"],
                    appName=game_data[str(app_id)]["data"]["name"],
                ).__dict__
                review_list[pageNum].append(review_dict)
                counter += 1
    # Process and filter reviews by date
    else:
        for i in range(len(reviews_array)):
            review_data = reviews_array[i]["reviews"]
            for i in range(len(review_data)):
                if counter == 5000:
                    review_list.append([])  # Start new page after 5000 reviews
                    counter = 0
                    pageNum += 1
                if (
                    datetime.datetime.strptime(date_filters[0], "%Y-%m-%d")
                    >= datetime.datetime.fromtimestamp(
                        review_data[i]["timestamp_created"]
                    )
                    >= datetime.datetime.strptime(date_filters[1], "%Y-%m-%d")
                ):
                    review_dict = Review(
                        author=review_data[i]["author"]["steamid"],
                        date=datetime.datetime.fromtimestamp(
                            review_data[i]["timestamp_created"]
                        ).strftime("%Y-%m-%d"),
                        hours=review_data[i]["author"]["playtime_at_review"],
                        content=review_data[i]["review"],
                        comments=review_data[i]["comment_count"],
                        source="steam",
                        helpful=review_data[i]["votes_up"],
                        funny=review_data[i]["votes_funny"],
                        recommend=review_data[i]["voted_up"],
                        franchise=game_data[str(app_id)]["data"]["developers"],
                        appName=game_data[str(app_id)]["data"]["name"],
                    ).__dict__
                    review_list.append(review_dict)
                    counter += 1
    print("\nSorting Reviews...")
    # Sort reviews by date and unique ID within each page
    for i in range(len(review_list)):
        review_list[i] = sorted(review_list[i], key=lambda x: (x["date"], x["id"]))
    return review_list


def get_user_input():
    """
    Handles all user input and returns the necessary data.
    """
    while True:
        print("\nHello! Welcome to the Steam Review Crawler.")
        print("\nPlease enter the app ID for the game you wish to crawl.")
        app_id = input("App ID: ")
        while not app_id.isdigit():
            print("That is not a whole number. (eg. 1382330) Please try again")
            app_id = input("Enter app id: ")
        # Verify if the app has reviews
        url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100&filter=recent"
        response = requests.get(url)
        review_data = response.json()
        if review_data["query_summary"]["num_reviews"] == 0:
            print(
                "\nThe app ID you inputted has no reviews. Please check the app ID and try again."
            )
            exit()
        else:
            break

    # Ask user how many reviews/pages to fetch
    filter = None
    date_filters = [None, None]
    numReviews = 0
    while True:
        print(
            "\nWould you like to fetch all or a number of pages reviews? (1 = 100 reviews) ('all' or a whole number) Note: Will fetch most recent reviews first"
        )
        filter = input("Enter:")
        if isinstance(filter, str) and filter.lower() == "all":
            numReviews = 0
            break
        elif filter.isdigit() and filter > 0:  # Use isdigit() to check for valid integer input
            numReviews = int(filter)
            break
        else:
            print("That is not a valid input. Try again.")

    # Ask if the user wants to filter reviews by date
    while True:
        print(
            "\nWould you like to filter the reviews between two dates? (y/yes or n/no)"
        )
        filter = input("Enter:")
        if filter.lower() == "y" or filter.lower() == "yes":
            while True:
                print("\nPlease enter the last date for the filter. (eg. YYYY-MM-DD)")
                date_filters[0] = input("Enter:")
                try:
                    dateobj = datetime.date.fromisoformat(date_filters[0])
                except ValueError:
                    print("That is not a valid response. Please try again.")
                except:
                    print("Something went wrong. Maybe you set the date to the future.")
                else:
                    if dateobj <= datetime.date.today():
                        break
                    else:
                        print("Date cannot be in the future.")
            while True:
                print(
                    "\nPlease enter the earliest date for the filter. (eg. YYYY-MM-DD)"
                )
                date_filters[1] = input("Enter:")
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

    return app_id, date_filters, numReviews


def main():
    # Main function to execute the script logic
    app_id, date_filters, numReviews = get_user_input()

    # Fetch game/app info and reviews from Steam
    app_data = fetch_app_data(app_id, date_filters, numReviews)
    review_array = organise_reviews(app_data[0], app_data[1], date_filters, app_id)

    # Ensure the "reviews" directory exists to save the data
    Path("reviews/").mkdir(parents=True, exist_ok=True)
    print(
        "\nSaving data to "
        + f'./reviews/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{str(app_id)}_page1_reviews.json +{len(review_array)-1 if (len(review_array)) >= 1 else ""} more'
    )
    cur_path = os.path.dirname(__file__)

    # Save review data to JSON files with dynamic filenames
    for i in range(len(review_array)):
        new_path = os.path.relpath(
            f'.\\reviews\\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{str(app_id)}_page{i+1}_reviews.json',
            cur_path,
        )
        with open(new_path, "w") as f:
            json.dump(review_array[i], f, indent=4)
        f.close()
    print(
        f"\nReviews for the {app_data[1][str(app_id)]['data']['type']} '{app_data[1][str(app_id)]['data']['name']}' (App ID: {app_id}) have been saved."
    )


if __name__ == "__main__":
    main()
