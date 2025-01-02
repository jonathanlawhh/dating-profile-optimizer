import dotenv
from tinder import Tinder
import os
import json
from openai import OpenAI
from pydantic import BaseModel

dotenv.load_dotenv()


class Suggestions(BaseModel):
    current: str
    suggestion: str
    example_for_bio: str
    example_from_potential_dates: str


class DateProfileSuggestion(BaseModel):
    suggestions: list[Suggestions]
    common_dates_interest: str


def get_suggestions(tinder_data: Tinder, match_style="potential") -> DateProfileSuggestion:
    """
    Return a list of suggestions based on Tinder data
    :param match_style: potential, teenager, senior_citizen, businessman
    :param tinder_data:
    :return: DateProfileSuggestion
    """
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    input_prompt: str = json.dumps({
        "dating_profile": tinder_data.profile,
        "potential_dates_profile": tinder_data.dates
    })

    match_style_options = {
        "potential": "the most potential dates profile",
        "teenager": "an 18 years old teenager profile",
        "senior_citizen": "a senior citizen profile",
        "businessman": "a busy businessman"
    }

    if match_style not in match_style_options:
        match_style = "potential"

    dev_prompt: str = ("You will receive a JSON that has a dating profile and potential dates profile. "
                       "Provide more than 5 suggestions on how to change the dating profile to match "
                       + match_style_options[match_style] +
                       ". Take into account the age, bio, common interest, section_name and any additional information deemed relevant to be compatible, "
                       "and example_from_potential_dates based on suggestion should have some names from potential dates for reference.")

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini" if os.getenv("OPENAI_MODEL") == "" else os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "developer", "content": dev_prompt},
            {"role": "user", "content": input_prompt}
        ],
        response_format=DateProfileSuggestion
    )

    suggestions: DateProfileSuggestion = completion.choices[0].message.parsed

    return suggestions


def http_optimize_profile(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    from flask import Response

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
        "Content-Type": "application/json"
    }

    # Set CORS headers for the preflight request
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for 3600s

        return Response({}, 201, headers=headers)

    req_data = request.get_json()

    if req_data is None or "profile" not in req_data:
        return Response("{'error': 'No parameters found'}")

    # Because it is a public API, we only allow loading dummy data
    treq = Tinder()

    treq.get_local_dates(req_data["country"] if req_data["country"] else "MY")
    treq.load_custom_profile(req_data["profile"])

    if treq.dates == [] or treq.profile == {}:
        return Response("{'error': 'No data returned'}", 400)

    # If there are no bio data, do not waste time and return a dummy response
    if treq.profile["user"]["bio"] == "":
        return Response(json.dumps({
            "suggestions": [
                {
                    "current": "No bio provided",
                    "suggestion": "Create a more engaging bio that showcases personality; include humor or interesting experiences.",
                    "example_for_bio": "Just a yoga enthusiast on a quest for the best avocado toast in town!",
                    "example_from_potential_dates": "Natas shares a playful bio about spaghetti being her love language."
                },
                {
                    "current": "Limited job info",
                    "suggestion": "Include more about your occupation or what you’re passionate about in your professional life.",
                    "example_for_bio": "Currently a freelance creative and always looking for inspiration.",
                    "example_from_potential_dates": "Syahi and Kyra mentioned their jobs, which adds to connection potential."
                },
                {
                    "current": "No common interests listed",
                    "suggestion": "Engage potential matches by adding common interests like 'Dining out' or 'Traveling'.",
                    "example_for_bio": "A foodie at heart who loves exploring new restaurants and traveling to unique places.",
                    "example_from_potential_dates": "Alici and Amali enjoy food tours and trying new cuisines."
                }
            ],
            "common_dates_interest": "Hiking and exploring coffee shops"
        }), status=200, headers=headers)

    req_suggestion: DateProfileSuggestion = get_suggestions(treq, "potential")
    req_suggestion_json = req_suggestion.json()

    return Response(req_suggestion_json, status=200, headers=headers)


def test_http_request():
    from flask import Flask, Request
    app = Flask(__name__)
    with app.app_context():
        data = {
            "profile": {
                "spotify": False,
                "traveling": False,
                "bio": "",
                "birth_date": "1999-01-01",
                "interest": ["IT", "Technology", "Science", "Engineering"],
                "descriptors": [],
                "job": {"company": "A Silicon Valley Comopany", "job_title": "Software Tester"}
            },
            "country": "JP"
        }

        request = Request.from_values(headers={'Content-Type': 'application/json'}, data=json.dumps(data))

    res = http_optimize_profile(request)
    print(res.data)


def optimize_profile_live():
    """
    Call this function to get suggestion from your Tinder profile
    :return:
    """
    t = Tinder()
    t.get_current_profile()
    t.get_dates()

    if t.dates == [] or t.profile == {}:
        print("Failed to get data")
        exit()

    sug = get_suggestions(t)
    print("Common dates interest: ", sug.common_dates_interest)
    print(" ")
    for s in sug.suggestions:
        print("Current :", s.current)
        print("Suggestion :", s.suggestion)
        print("Example :", s.example_for_bio)
        print("Potential dates :", s.example_from_potential_dates)
        print(" ")


if __name__ == "__main__":
    # optimize_profile_live()
    # test_http_request()
    print("eh")
