import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid
from main import Review, fetch_app_data, organise_reviews


class TestReviewClass(unittest.TestCase):
    def test_generate_id(self):
        # Test the generate_id method
        review = Review(
            author="author123",
            date="2023-10-07",
            hours=100,
            content="Great game!",
            comments=5,
            source="steam",
            helpful=10,
            funny=2,
            recommend=True,
            franchise="GameDev",
            appName="CoolGame",
        )
        expected_id = review.generate_id("CoolGame", "Great game!", "author123")
        self.assertEqual(review.id, expected_id)

    def test_review_initialization(self):
        # Test the initialization of Review objects
        review = Review(
            author="author123",
            date="2023-10-07",
            hours=100,
            content="Great game!",
            comments=5,
            source="steam",
            helpful=10,
            funny=2,
            recommend=True,
            franchise="GameDev",
            appName="CoolGame",
        )
        self.assertEqual(
            review.author, str(uuid.uuid5(uuid.NAMESPACE_DNS, "author123"))
        )
        self.assertEqual(review.date, "2023-10-07")
        self.assertEqual(review.hours, 100)
        self.assertEqual(review.content, "Great game!")
        self.assertEqual(review.comments, 5)
        self.assertTrue(review.recommend)


class TestFetchAppData(unittest.TestCase):
    @patch("main.requests.get")
    def test_fetch_app_data_success(self, mock_get):
        # Mock response for reviews
        mock_reviews_response = MagicMock()
        mock_reviews_response.json.return_value = {
            "query_summary": {"num_reviews": 1},
            "reviews": [
                {
                    "author": {"steamid": "123456", "playtime_at_review": 10},
                    "timestamp_created": 1633305600,  # Example Unix timestamp
                    "review": "Good game",
                    "comment_count": 3,
                    "votes_up": 10,
                    "votes_funny": 5,
                    "voted_up": True,
                }
            ],
            "cursor": "*",
            "success": True,
        }

        # Mock response for game info
        mock_game_response = MagicMock()
        mock_game_response.json.return_value = {
            "123456": {
                "success": True,
                "data": {"name": "CoolGame", "developers": ["GameDev"], "type": "game"},
            }
        }

        # Set the mock side effects (what the mock will return when called)
        mock_get.side_effect = [mock_reviews_response, mock_game_response]

        # Define input parameters
        app_id = 123456
        date_filters = [None, None]
        numReviews = 1

        # Call the function under test
        reviews, game_data = fetch_app_data(app_id, date_filters, numReviews)

        # Assertions to verify behavior
        self.assertEqual(len(reviews), 1)
        self.assertIn("CoolGame", game_data[str(app_id)]["data"]["name"])
        self.assertTrue(game_data[str(app_id)]["success"])


class TestOrganiseReviews(unittest.TestCase):
    def test_organise_reviews(self):
        # Mock review data structure that matches what organise_reviews expects
        mock_reviews = [
            {
                "reviews": [
                    {
                        "author": {"steamid": "123456", "playtime_at_review": 10},
                        "timestamp_created": 1633305600,  # Example Unix timestamp
                        "review": "Good game",
                        "comment_count": 3,
                        "votes_up": 10,
                        "votes_funny": 5,
                        "voted_up": True,
                    }
                ]
            }
        ]

        # Mock game data structure that matches what organise_reviews expects
        mock_game_data = {
            "123456": {
                "data": {"name": "CoolGame", "developers": "GameDev", "type": "game"}
            }
        }

        # Define the input parameters
        date_filters = [None, None]  # No date filters applied
        app_id = 123456  # Example app ID

        # Call the function under test
        review_list = organise_reviews(
            mock_reviews, mock_game_data, date_filters, app_id
        )

        # Assert that the review_list is correctly formatted and contains the expected data
        self.assertEqual(len(review_list), 1)  # One page of reviews
        self.assertEqual(len(review_list[0]), 1)  # One review in the first page
        self.assertEqual(review_list[0][0]["content"], "Good game")  # Review content
        self.assertEqual(review_list[0][0]["appName"], "CoolGame")  # App name


if __name__ == "__main__":
    unittest.main()
