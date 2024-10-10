import asyncio
import aiohttp
import datetime
import hashlib
import json
import requests
import urllib.parse
import uuid
from itertools import count
from pathlib import Path
from typing import List, Dict, Tuple, Union, Any


class Review:
    def __init__(
        self,
        author: str,
        date: str,
        hours: int,
        content: str,
        comments: int,
        source: str,
        helpful: int,
        funny: int,
        recommend: bool,
        franchise: Union[str, List[str]],  # Allows for multiple developers
        appName: str,
    ):
        """
        Represents a single Steam review.

        Attributes:
            id (str): A unique ID for the review, generated using SHA-256 hashing.
            author (str): The author's Steam ID (hashed with UUID5).
            date (str): The date of the review (YYYY-MM-DD format).
            hours (int): The number of hours the author played the game/app.
            content (str): The text content of the review.
            comments (int): The number of comments on the review.
            source (str): The source of the review (e.g., "steam").
            helpful (int): The number of users who found the review helpful.
            funny (int): The number of users who found the review funny.
            recommend (bool): Whether the author recommends the game/app.
            franchise (str): The name of the game/app's developer (or a list of developers).
            appName (str): The name of the game/app.
        """
        self.id = self.generate_id(appName, content, author)
        self.author = str(uuid.uuid5(uuid.NAMESPACE_DNS, author))
        self.date = date
        self.hours = hours
        self.content = content
        self.source = source
        self.comments = comments
        self.helpful = helpful
        self.funny = funny
        self.recommend = recommend
        self.franchise = franchise
        self.appName = appName

    def generate_id(self, appName: str, content: str, author: str) -> str:
        """
        Generates a unique ID for the review using SHA-256 hashing.

        Args:
            appName (str): The name of the game/app.
            content (str): The review text.
            author (str): The author's Steam ID.

        Returns:
            str: The unique review ID.
        """
        # Combine review fields and normalise
        id_string = f"{appName}-{content}-{author}".lower()
        # Apply SHA-256 hashing
        hash_object = hashlib.sha256(id_string.encode("utf-8"))
        return hash_object.hexdigest()


async def fetch_app_data(
    app_id: int, review_count: int
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Fetches reviews and app information from the Steam API asynchronously.

    Args:
        app_id (int): The Steam app ID.
        numReviews (int): The number of reviews to fetch.
                         0 fetches all reviews.

    Returns:
        tuple: A tuple containing a list of reviews and a dictionary of
               app information. Returns "reviews not found" if there is an error.
    """
    found = 0  # Keeps track of how many reviews are found
    reviews = []  # List to store review data
    cursor = "*"  # Cursor to paginate through the Steam API's review pages

    print("\nFetching Reviews... (this may take a bit)")

    async with aiohttp.ClientSession() as session:
        # Determine the loop type based on numReviews
        if review_count == 0:
            loop_type = count(0)  # Infinite loop for all reviews
        else:
            loop_type = range(review_count)  # Loop for a specific number of reviews

        # Combined loop for fetching reviews
        for _ in loop_type:
            url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100&filter=recent&purchase_type=all&cursor={cursor}"
            async with session.get(url) as response:
                try:
                    review_data = await response.json()
                except aiohttp.ClientError as e:
                    print(f"Error fetching reviews: {e}")
                    return "reviews not found"
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON response: {e}")
                    return "reviews not found"

            if review_data["query_summary"]["num_reviews"] == 0:
                break

            cursor = urllib.parse.quote_plus(review_data["cursor"].encode())
            reviews.extend(review_data["reviews"])
            found += len(review_data["reviews"])

            print("Found {} so far...".format(found), end="\r")

    # Fetch info
    print("Fetching App Info...")
    url = "http://store.steampowered.com/api/appdetails?appids={}".format(app_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                game_data = await response.json()
            except aiohttp.ClientError as e:
                print(f"Error fetching reviews: {e}")
                return "reviews not found"
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                return "reviews not found"

    if (
        "success" in review_data
        and review_data["success"]
        and "success" in game_data[str(app_id)]
        and game_data[str(app_id)]["success"]
    ):
        data = (reviews, game_data)
        print(f"Fetched {found} reviews and app info")
        return data
    else:
        return "reviews not found"


async def organise_reviews(
    reviews_array: List[Dict[str, Any]],
    game_data: Dict[str, Any],
    date_filters: List[Union[str, None]],
    app_id: int,
) -> List[List[Dict[str, Any]]]:
    """
    Organizes fetched reviews into Review objects, applies date filtering,
    and sorts them.

    Args:
        reviews_array (list): A list of dictionaries containing review data.
        game_data (dict): A dictionary containing app information.
        date_filters (list): A list of two date strings (YYYY-MM-DD format)
                             to filter reviews by date range. None if no filter.
        app_id (int): The Steam app ID.

    Returns:
        list: A list of lists, where each inner list contains Review objects
              for a single page (max 5000 reviews per page).
    """
    print("\nConverting Reviews into Objects...")

    if date_filters != [None, None]:
        start_date = datetime.datetime.strptime(date_filters[0], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(date_filters[1], "%Y-%m-%d")

    # Convert reviews to Review objects and apply date filtering using list comprehension
    review_list = []
    for review in reviews_array:
        review_date = datetime.datetime.fromtimestamp(review["timestamp_created"])
        if date_filters == [None, None] or start_date >= review_date >= end_date:
            try:
                franchise = game_data[str(app_id)]["data"]["developers"]
            except KeyError:
                franchise = "Unknown"

            review_list.append(
                Review(
                    author=review["author"]["steamid"],
                    date=review_date.strftime("%Y-%m-%d"),
                    hours=review["author"]["playtime_at_review"],
                    content=review["review"],
                    comments=review["comment_count"],
                    source="steam",
                    helpful=review["votes_up"],
                    funny=review["votes_funny"],
                    recommend=review["voted_up"],
                    franchise=franchise,
                    appName=game_data[str(app_id)]["data"]["name"],
                ).__dict__
            )

    print("\nSorting Reviews...")
    # Sort reviews by date and unique ID
    review_list = sorted(review_list, key=lambda x: (x["date"], x["id"]))

    # Paginate reviews (5000 reviews per page)
    paged_reviews = [
        review_list[i : i + 5000] for i in range(0, len(review_list), 5000)
    ]

    return paged_reviews


def get_app_id() -> int:
    while True:
        print("\nHello! Welcome to the Steam Review Crawler.")
        print("\nPlease enter the app ID for the game you wish to crawl.")
        app_id = input("App ID: ")
        while not isinstance(app_id, int):
            print("That is not a whole number. (eg. 1382330) Please try again")
            app_id = input("Enter app id: ")

        # Verify if the app has reviews
        url = "https://store.steampowered.com/appreviews/{}?json=1&num_per_page=100&filter=recent".format(
            app_id
        )
        response = requests.get(url)
        review_data = response.json()
        if review_data["query_summary"]["num_reviews"] == 0:
            print(
                "\nThe app ID you inputted has no reviews. Please check the app ID and try again."
            )
            exit()
        else:
            return app_id


def get_review_count() -> int:
    # Ask user how many reviews/pages to fetch
    while True:
        print(
            "\nWould you like to fetch all or a number of pages reviews? (1 = 100 reviews) ('all' or a whole number) Note: Will fetch most recent reviews first"
        )
        review_count = input("Enter: ")
        if isinstance(review_count, str) and review_count.lower() == "all":
            review_count = 0
            return review_count
        elif isinstance(review_count, int) and review_count > 0:
            return review_count
        else:
            print("That is not a valid input. Try again.")


def get_date_filter():
    # Ask if the user wants to filter reviews by date
    date_filters = [None, None]
    while True:
        print(
            "\nWould you like to filter the reviews between two dates? (y/yes or n/no)"
        )
        filter_response = input("Enter: ")
        if filter_response.lower() in ("y", "yes"):
            while True:
                print("\nPlease enter the end date for the filter. (eg. YYYY-MM-DD)")
                end_date = input("Enter: ")
                try:
                    dateobj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    print("That is not a valid response. Please try again.")
                except:
                    print("Something went wrong. Maybe you set the date to the future.")
                else:
                    if dateobj <= datetime.datetime.today():
                        date_filters[0] = end_date
                        break
                    else:
                        print("Date cannot be in the future.")
            while True:
                print("\nPlease enter the start date for the filter. (eg. YYYY-MM-DD)")
                start_date = input("Enter: ")
                try:
                    dateobj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    print("That is not a valid response. Please try again.")
                except:
                    print("Something went wrong. Maybe you set the date to the future.")
                else:
                    if dateobj <= datetime.datetime.today():
                        date_filters[1] = start_date
                        break
                    else:
                        print("Date cannot be in the future.")
            break
        elif filter_response.lower() in ("n", "no"):
            break
        else:
            print("That is not a valid response. Please try again")

    return date_filters


async def main():
    """
    Main function to run the Steam review crawler.
    """
    app_id = get_app_id()
    review_count = get_review_count()
    date_filter = get_date_filter()

    # Fetch game/app info and reviews from Steam
    app_data = await fetch_app_data(app_id, review_count)
    if app_data == "reviews not found":
        print("Exiting due to error fetching data.")
        return

    review_array = await organise_reviews(
        app_data[0], app_data[1], date_filter, app_id
    )

    # Ensure the "reviews" directory exists to save the data
    Path("reviews").mkdir(parents=True, exist_ok=True)
    print(
        "\nSaving data to "
        + f'./reviews/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{str(app_id)}_page1_reviews.json +{len(review_array)-1 if (len(review_array)) >= 1 else ""} more'
    )

    # Save review data to JSON files with dynamic filenames
    for i in range(len(review_array)):
        new_path = (
            Path("reviews")
            / f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{str(app_id)}_page{i+1}_reviews.json'
        )
        with open(new_path, "w") as f:
            json.dump(review_array[i], f, indent=4)
    print(
        f"\nReviews for the {app_data[1][str(app_id)]['data']['type']} '{app_data[1][str(app_id)]['data']['name']}' (App ID: {app_id}) have been saved."
    )


if __name__ == "__main__":
    asyncio.run(main())
