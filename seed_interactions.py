import re
import requests
import urllib.parse
from time import sleep

BASE_URL = "http://127.0.0.1:8000/api/v1"
USER_SEED_FILE = "user_seed.md"


def parse_users_from_seed(filename):
    """Parses user data from the markdown seed file."""
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    users_data = content.strip().split("---")
    users = []

    for user_data in users_data:
        user_data = user_data.strip()
        if not user_data:
            continue

        user = {}
        try:
            user["full_name"] = re.search(r"### User \d+:\s*(.*)", user_data).group(1)
            user["email"] = re.search(r"-\s+\*\*Email\*\*:\s*(.*)", user_data).group(1)
            user["password"] = re.search(r"-\s+\*\*Password\*\*:\s*(.*)", user_data).group(1)
            user["gender"] = re.search(r"-\s+\*\*Gender\*\*:\s*(.*)", user_data).group(1)
            
            movies_raw_match = re.search(r"-\s+\*\*Liked Movies\*\*:(.*)", user_data, re.DOTALL)
            if not movies_raw_match:
                raise ValueError("Could not find liked movies list.")
            
            movies_raw = movies_raw_match.group(1).strip()
            movies = [re.sub(r"^\s*\d+\.\s*", "", movie).strip() for movie in movies_raw.split("\n") if movie.strip()]
            user["liked_movies"] = movies

            users.append(user)
        except (AttributeError, ValueError) as e:
            print(f"Skipping a malformed user block. Error: {e}")
            print(f"Block content: {user_data[:200]}...")


    return users


def register_or_login(session, user):
    """Registers a new user or logs in if the user already exists."""
    
    gender_map = {"female": 0, "male": 1, "other": 2}
    gender_value = gender_map.get(user["gender"].lower(), 2) # Default to 'Other'

    register_payload = {
        "email": user["email"],
        "name": user["full_name"],
        "password": user["password"],
        "gender": gender_value,
    }
    
    print(f"--- Processing user: {user['full_name']} ({user['email']}) ---")
    
    # Try to register
    print("Attempting to register...")
    response = session.post(f"{BASE_URL}/auth/register", json=register_payload)

    if response.status_code in [200, 201]:
        print("Registration successful.")
        return response.json()["access_token"]
    elif response.status_code == 400 and "already registered" in response.text:
        print("User already exists. Attempting to log in...")
        login_payload = {"email": user["email"], "password": user["password"]}
        response = session.post(f"{BASE_URL}/auth/login", json=login_payload)
        
        if response.status_code == 200:
            print("Login successful.")
            return response.json()["access_token"]
        else:
            print(f"Login failed! Status: {response.status_code}, Response: {response.text}")
            return None
    else:
        print(f"Registration failed! Status: {response.status_code}, Response: {response.text}")
        return None


def search_movie_and_get_id(session, movie_title, access_token):
    """Searches for a movie by title and returns its ID."""
    headers = {"Authorization": f"Bearer {access_token}"}
    encoded_query = urllib.parse.quote(movie_title)
    search_url = f"{BASE_URL}/movies/search?query={encoded_query}&limit=1"
    
    response = session.get(search_url, headers=headers)

    if response.status_code == 200:
        results = response.json()
        if results and len(results) > 0:
            movie_id = results[0].get("_id")
            print(f"Found '{movie_title}' -> Movie ID: {movie_id}")
            return movie_id
        else:
            print(f"Movie not found: '{movie_title}'")
            return None
    else:
        print(f"Failed to search for movie '{movie_title}'. Status: {response.status_code}")
        return None

def like_movie(session, movie_id, access_token):
    """Likes a movie by its ID using the toggle endpoint."""
    if not movie_id:
        return
        
    headers = {"Authorization": f"Bearer {access_token}"}
    like_url = f"{BASE_URL}/interactions/{movie_id}/like"
    
    response = session.post(like_url, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        action = response_data.get("action")
        if action == "added":
            print(f"Successfully liked movie {movie_id}.")
        elif action == "removed":
            # This means the movie was already liked, and the toggle removed it.
            # We want to ensure it's liked, so we should add it back.
            # However, to avoid infinite loops and keep the seeding simple,
            # we will just log this event. The goal is to seed interactions,
            # and a toggle is one interaction.
            print(f"Movie {movie_id} was already liked, so the toggle action removed the like. Leaving it as is.")
        else:
             print(f"An unexpected action '{action}' was returned for movie {movie_id}.")
    else:
        print(f"Failed to interact with movie {movie_id}. Status: {response.status_code}, Response: {response.text}")


def main():
    """Main function to run the interaction seeding script."""
    users = parse_users_from_seed(USER_SEED_FILE)
    if not users:
        print("No users found or parsed from the seed file. Exiting.")
        return

    with requests.Session() as session:
        for user in users:
            access_token = register_or_login(session, user)

            if not access_token:
                print(f"Could not get access token for {user['email']}. Skipping this user.")
                continue

            print(f"Starting to like movies for {user['full_name']}...")
            for movie_title in user["liked_movies"]:
                # Added a small delay to avoid overwhelming the server
                sleep(0.5)
                # The year part in "Movie Title (YYYY)" can sometimes hurt search results. Let's remove it.
                movie_name_only = re.sub(r"\s\(\d{4}\)$", "", movie_title).strip()
                movie_id = search_movie_and_get_id(session, movie_name_only, access_token)
                if movie_id:
                    like_movie(session, movie_id, access_token)
            
            print(f"Finished processing movies for {user['full_name']}.\n")

    print("--- All users processed. Script finished. ---")


if __name__ == "__main__":
    main() 