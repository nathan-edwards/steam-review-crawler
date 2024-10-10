import json
import unittest
import asyncio
from unittest.mock import patch, AsyncMock
import datetime
import hashlib
import uuid

import aiohttp
from main import Review, fetch_app_data, organise_reviews

# Sample data for testing
mock_review_data = {
    "reviews": [
        {
            "author": {"steamid": "123456789", "playtime_at_review": 10},
            "timestamp_created": 1678886400,  # 2023-03-15
            "review": "This game is awesome!",
            "comment_count": 2,
            "votes_up": 100,
            "votes_funny": 5,
            "voted_up": True,
        }
    ],
    "query_summary": {"num_reviews": 1},
    "cursor": "next_cursor",
    "success": True,
}

mock_game_data = {
    "12345": {
        "success": True,
        "data": {
            "name": "Test Game",
            "developers": ["Test Dev"],
            "type": "game",
        },
    }
}


class TestReview(unittest.IsolatedAsyncioTestCase):
    def test_generate_id(self):
        review = Review(
            author="testuser",
            date="2024-01-01",
            hours=5,
            content="Test review",
            comments=0,
            source="steam",
            helpful=0,
            funny=0,
            recommend=True,
            franchise="Test Franchise",
            appName="Test App",
        )
        #  Combine review fields and normalise (use the hashed author)
        id_string = f"{review.appName}-{review.content}-{review.author}".lower() 
        # Apply SHA-256 hashing
        hash_object = hashlib.sha256(id_string.encode("utf-8"))
        expected_id = hash_object.hexdigest()
        self.assertEqual(review.id, expected_id) 

    @patch("aiohttp.ClientSession.get")
    async def test_fetch_app_data_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(
            side_effect=[mock_review_data, mock_game_data]
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        app_id = 12345
        review_count = 10
        reviews, game_data = await fetch_app_data(app_id, review_count)

        self.assertEqual(len(reviews), 1)
        self.assertEqual(game_data, mock_game_data)

    @patch("aiohttp.ClientSession.get")
    async def test_fetch_app_data_no_reviews(self, mock_get):
        mock_review_data_copy = mock_review_data.copy()
        mock_review_data_copy["query_summary"]["num_reviews"] = 0
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(
            side_effect=[mock_review_data_copy, mock_game_data]
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        app_id = 12345
        review_count = 10
        result = await fetch_app_data(app_id, review_count)

        self.assertEqual(result, "reviews not found")

    @patch("aiohttp.ClientSession.get")
    async def test_fetch_app_data_client_error(self, mock_get):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(side_effect=aiohttp.ClientError)
        mock_get.return_value.__aenter__.return_value = mock_response

        app_id = 12345
        review_count = 10
        result = await fetch_app_data(app_id, review_count)

        self.assertEqual(result, "reviews not found")

    @patch("aiohttp.ClientSession.get")
    async def test_fetch_app_data_json_error(self, mock_get):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("", "", 0))
        mock_get.return_value.__aenter__.return_value = mock_response

        app_id = 12345
        review_count = 10
        result = await fetch_app_data(app_id, review_count)

        self.assertEqual(result, "reviews not found")

    async def test_organise_reviews_no_date_filter(self):
        app_id = 12345
        date_filters = [None, None]
        paged_reviews = await organise_reviews(
            mock_review_data["reviews"], mock_game_data, date_filters, app_id
        )

        self.assertEqual(len(paged_reviews), 1)
        self.assertEqual(len(paged_reviews[0]), 1)
        self.assertEqual(paged_reviews[0][0]["appName"], "Test Game")

    async def test_organise_reviews_with_date_filter(self):
        app_id = 12345
        date_filters = ["2023-03-10", "2023-03-20"]
        paged_reviews = await organise_reviews(
            mock_review_data["reviews"], mock_game_data, date_filters, app_id
        )

        self.assertEqual(len(paged_reviews), 1)
        self.assertEqual(len(paged_reviews[0]), 1)
        self.assertEqual(paged_reviews[0][0]["appName"], "Test Game")

    async def test_organise_reviews_empty(self):
        app_id = 12345
        date_filters = [None, None]
        paged_reviews = await organise_reviews([], mock_game_data, date_filters, app_id)
        self.assertEqual(paged_reviews, [[]])  # Expect a list containing an empty list


if __name__ == "__main__":
    unittest.main()