import json
import logging
import os
import time
import datetime
import requests


def _log_output(data: dict | list, output_name: str):
    """
    If FLAG_DEVELOPMENT is TRUE, save an output
    :param data:
    :param output_name: File name to output
    :return:
    """
    if os.getenv("FLAG_DEVELOPMENT") == "TRUE" or os.getenv("FLAG_DATA_GATHERING") == "TRUE":
        os.makedirs(os.path.dirname(output_name), exist_ok=True)
        with open(output_name, "w") as outfile:
            outfile.write(json.dumps(data))


def _read_local_file(fp: str):
    """
    Function to read a local JSON file
    :param fp:
    :return:
    """
    with open(fp, "r") as rf:
        file_content = json.load(rf)

    return file_content


class Tinder:
    __X_AUTH_TOKEN: str  # Browser console: window.localStorage["TinderWeb/APIToken"]
    __APP_SESSION_ID: str = "000000"
    __API_LINK: str
    __DATES_ITER: int = 5
    __API_INTERVAL: int = 60  # seconds

    # Output file names
    __FP_PROFILE = "./local_private_data/profile.json"
    __FP_DATES = "./local_data/potential_dates_NL.json"

    profile = {
        "spotify": {"spotify_connected": False},
        "travel": {"is_traveling": False},
        "user": {}
    }

    dates: list = []

    def __init__(self, x_auth=None):
        self.__X_AUTH_TOKEN = x_auth if x_auth is not None else os.getenv("X_AUTH_TOKEN")
        self.__API_LINK = os.getenv("TINDER_API_ENDPOINT")

        now = datetime.datetime.now()
        # Some random ID?
        self.__APP_SESSION_ID = now.strftime("%Y%m%d%H%M-b%S%M%d-a%Y%S-c%S%S%H%M")

    def get_current_profile(self):
        """
        Get current user profile
        :return:
        """
        if os.getenv("FLAG_USE_LOCAL_DATA") == "TRUE":
            self.profile = _read_local_file(self.__FP_PROFILE)
            return

        include_field = [
            # "available_descriptors",
            # "contact_cards",
            # "feature_access",
            "instagram", "likes", "profile_meter", "spotify",
            # "super_likes", "tinder_u",
            "travel", "user"
            # , "all_in_gender"
        ]

        res = requests.get(
            self.__API_LINK + "/profile?locale=en&include=" + ",".join(include_field),
            headers={
                "accept": "application/json",
                "x-auth-token": self.__X_AUTH_TOKEN,
                "app-session-id": self.__APP_SESSION_ID
            }
        )

        if res.status_code != 200:
            self.profile = {}
            return {}

        self.profile = res.json()["data"]

        self.profile = self._recurse_data_cleaning(self.profile)

        _log_output(self.profile, self.__FP_PROFILE)

    def get_dates(self):
        """
        Get potential dates
        :return:
        """
        if os.getenv("FLAG_USE_LOCAL_DATA") == "TRUE":
            self.dates = _read_local_file(self.__FP_DATES)
            return

        for i in range(self.__DATES_ITER):
            res = requests.get(
                self.__API_LINK + "/recs/core?locale=en",
                headers={
                    "accept": "application/json",
                    "x-auth-token": self.__X_AUTH_TOKEN,
                    "app-session-id": self.__APP_SESSION_ID
                }
            )

            if res.status_code != 200:
                # If not 200, terminate
                print(res.status_code)
                self.dates = []
                return []

            if 'timeout' in res.json()["data"]:
                # If timeout, just break out of the loop. There could be previous data
                logging.error(res.json()["data"]["timeout"])
                break

            print("Run dates complete iteration " + str(i))
            self.dates = self.dates + res.json()["data"]["results"]
            time.sleep(self.__API_INTERVAL)

        self._remove_duplicate_dates()
        self.dates = self._recurse_data_cleaning(self.dates)

        tn = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        tmp_filename = "./local_data/potential_dates_" + tn + ".json"
        _log_output(self.dates, tmp_filename)
        print("Total dates :" + len(self.dates).__str__())

    def _recurse_data_cleaning(self, data: list | dict) -> list | dict:
        """
        Recursively cleans a dictionary by removing specified keys and
        deeply cleaning nested dictionaries.

        Args:
            data: The dictionary/list to clean.

        Returns:
            The cleaned dictionary/list.
        """
        user_do_not_neet_keys = ["id", "_id", "url", "icon_url", "icon_urls", "section_id", "match_group_key",
                                 "image_url", "content_hash",
                                 # keys from get_dates
                                 "online_now", "type", "tapped_action", "images", "preview_url", "uri",
                                 "profile_detail_content", "tappy_content", "facebook", "section_name",
                                 "ui_configuration", "badges", "is_superlike_upsell", "hidden_intent",
                                 "s_number", "user_posts", "distance_mi", "is_common", "answer_id",

                                 # keys from profile
                                 "available_descriptors", "available_interests", "likes",
                                 "descriptor_choice_id", "global_mode", "billing_info", "crm_id",
                                 "autoplay_video", "photos", "create_date", "mm_enabled", "noonlight_protected",
                                 "recommended_sort_discoverable", "sparks_quizzes", "ping_time", "phone_id"]

        if isinstance(data, list):
            i = 0
            for d in data:
                if isinstance(d, dict) or isinstance(d, list):
                    data[i] = self._recurse_data_cleaning(d)

                i += 1

            return data

        cleaned_data = {}
        for key, value in data.items():
            if key not in user_do_not_neet_keys:
                if isinstance(value, dict) or isinstance(value, list):
                    # If it is an empty list, skip it, we do not want to waste our tokens
                    if isinstance(value, list) and len(value) == 0:
                        continue
                    cleaned_data[key] = self._recurse_data_cleaning(value)
                else:
                    cleaned_data[key] = value

        return cleaned_data

    def _remove_duplicate_dates(self):
        """
        If the API ever return duplicates, remove it. Because useless data waste token.
        :return:
        """
        found_id = {}
        tmp_dates = []

        for s in self.dates:
            if s["user"]["_id"] in found_id:
                continue

            # If in data gathering mode, obfuscate some data from online bots
            if os.getenv("FLAG_DATA_GATHERING") == "TRUE":
                # Truncate name
                s["user"]["name"] = s["user"]["name"][:5]

            found_id[s["user"]["_id"]] = 1
            tmp_dates.append(s)

        self.dates = tmp_dates

    def get_local_dates(self, country: str):
        """
        Load a local list of potential dates without grabbing from API

        :param country: 2 digit country code, default to MY
        :return:
        """
        fp = "potential_dates_sample.json"
        configured_countries = ["DE", "JP", "NL", "MY"]

        if country.upper() in configured_countries:
            fp = "./local_data/potential_dates_" + country.upper() + ".json"

        self.dates = _read_local_file(fp)

    def load_custom_profile(self, profile):
        """
        Load a customized profile rather than grabbing from API

        :param profile: {
                spotify: True,
                traveling: True,
                bio: "",
                birth_date: "",
                interest: [],
                descriptors: [],
                job: { company: "", job_title: "" }
            }
        :return: self.profile
        """
        self.profile = {
            "spotify": {"spotify_connected": profile["spotify"] if "spotify" in profile else False},
            "travel": {"is_traveling": profile["traveling"] if "traveling" in profile else False},
            "user": {
                "age_filter_max": 30,
                "age_filter_min": 18,
                "bio": profile["bio"] if "bio" in profile else "",
                "birth_date": profile["birth_date"] if "birth_date" in profile else "1995-01-01T00:00:00.000Z",
                "user_interests": {
                    "selected_interests": []
                },
                "selected_descriptors": [],
                "jobs": []
            }
        }

        if "interest" in profile and len(profile["interest"]) > 0:
            self.profile["user"]["user_interests"]["selected_interests"] = [{"name": interest} for interest in
                                                                            profile["interest"]]

        if "descriptors" in profile and len(profile["descriptors"]) > 0:
            self.profile["user"]["selected_descriptors"] = [{"visibility": "public", "choice_selections": desc} for desc
                                                            in profile["descriptors"]]

        if "job" in profile:
            self.profile["user"]["jobs"] = [
                {
                    "company": {
                        "displayed": True,
                        "name": profile["job"]["company"] if "company" in profile["job"] else ""
                    },
                    "title": {
                        "displayed": True,
                        "name": profile["job"]["job_title"] if "job_title" in profile["job"] else ""
                    }
                }
            ]
