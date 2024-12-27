import os
import requests
import mal_oauth as MALoauth
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch client ID from the environment
CLIENT_ID = os.getenv('MAL_CLIENT_ID')
BASE_URL = "https://api.myanimelist.net/v2"

# Obtain oath token
oath_token = MALoauth.get_valid_token()




# GET METHODS
def get_anime_list(query, limit=10):
    """
    Fetches a list of anime from the MyAnimeList API.

    Args:
        query (str): The search query for anime.
        limit (int): Number of results to return (default: 10).

    Returns:
        list: A list of anime dictionaries with relevant details.
    """
    url = f"{BASE_URL}/anime/?q={query}&limit={limit}"
    headers = {
        "X-MAL-CLIENT-ID": CLIENT_ID  # Use CLIENT_ID from environment
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []


def get_anime_ranking(limit=10):
    """
    Fetches the top anime from the MyAnimeList API.

    Args:
        limit (int): Number of results to return (default: 10).

    Returns:
        list: A list of anime dictionaries with relevant details.
    """
    url = f"{BASE_URL}/anime/ranking"
    headers = {
        "X-MAL-CLIENT-ID": CLIENT_ID  # Use CLIENT_ID from environment
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("data", [])[:limit]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []



def get_user_anime_list(username, fields="list_status, finish_date", sort="list_score", limit=10, offset=0,):
    """
    Fetches a user's anime list from the MyAnimeList API.

    Args:
        username (str): The username of the user.
        limit (int): Number of results to return (default: 10).
        fields (str): Fields to return (default: "list_status", which lists the scores given).
        sort (str): Sort order of the list (default: "list_score", others: "list_updated_at", "anime_title", "anime_start_date").

        List of fields: id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics

    Returns:
        list: A list of anime dictionaries with relevant details.
    """
    url = f"{BASE_URL}/users/{username}/animelist?fields={fields}&sort={sort}&limit={limit}&offset={offset}"
    headers = {
        "X-MAL-CLIENT-ID": CLIENT_ID  # Use CLIENT_ID from environment
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("data", [])[:limit]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []
    

# PATCH METHODS
def update_anime_status(animeId: int, status: str = None, is_rewatching: bool = None, score: int = None, 
                        num_eps_watched: int = None, num_rewatches: int = None, tags: str = None, 
                        comments: str = None, start_date: str = None, finish_date: str = None):
    """
    Updates the status of an anime in the user's list on MyAnimeList.

    Args:
        animeId (int): The ID of the anime to update.
        status (str, optional): The status of the anime (watching, completed, on_hold, dropped, plan_to_watch).
        is_rewatching (bool, optional): Whether the anime is being rewatched.
        score (int, optional): The score given to the anime (0-10).
        num_eps_watched (int, optional): The number of episodes watched.
        num_rewatches (int, optional): The number of rewatches.
        tags (str, optional): List of tags for the anime.
        comments (str, optional): Comments or review for the anime.
        start_date (str, optional): The date when the anime was started (YYYY-MM-DD).
        finish_date (str, optional): The date when the anime was finished (YYYY-MM-DD).

    Returns:
        dict: Response from the API.
    """
    url = f"{BASE_URL}/anime/{animeId}/my_list_status"
    headers = {
        "Authorization": f"Bearer {oath_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {k: v for k, v in {
        "status": status,
        "is_rewatching": is_rewatching,
        "score": score,
        "num_watched_episodes": num_eps_watched,
        "num_times_rewatched": num_rewatches,
        "tags": tags,
        "comments": comments,
        "start_date": start_date,
        "finish_date": finish_date
    }.items() if v is not None}
    
    response = requests.patch(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {}


# Function to populate finish date fields with last list edit date
def correct_anime_finish_dates(username: str):
    num_updated = 0

    # 1. Get the user's anime list with update date fields
    user_anime_list = get_user_anime_list(username, fields="list_status", sort="anime_title", limit= 1000)

    # 2. Loop through the anime list and update finish date with list updated date
    for anime in user_anime_list:
        if anime.get("list_status"):
            # only update if the anime doesn't have a finish date & is completed
            if not anime["list_status"].get("finish_date") and anime["list_status"].get("status") == "completed":
                new_finish_date = anime["list_status"].get("updated_at") 
                new_finish_date = new_finish_date.split('T')[0]
                if new_finish_date:
                    anime_id = anime["node"]["id"]
                    response = update_anime_status(anime_id, finish_date=new_finish_date)
                    if response:
                        num_updated += 1
                    else:
                        print(f"Error updating finish date for anime ID: {anime_id}")

    # 3. Updated list
    updated_list = get_user_anime_list(username, fields="list_status", sort="anime_title", limit=5)
    print(json.dumps(updated_list, indent=4))

    print(f"Updating finish dates for {num_updated} of {len(user_anime_list)} anime entries...")
    