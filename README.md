# Dating profile optimizer using ChatGPT

[[`Project Writeup`](https://medium.com/@jonathanlawhh) [`My Website`](https://jonathanlawhh.com/)]

## Project Overview

This project explores the use of large language models (ChatGPT for now) to "fine-tune" the dating profile of a user
based on surrounding potential dates.
It also serves as a proof of concept that online presence can be manipulated easily and convincingly.

**Notice**

The online demo application at [dating.jonathanlawhh.com](https://dating.jonathanlawh.com) only serves limited truncated
and obfuscated data.

To run suggestion based on your own profile and real potential dates around you, you would have to run this project
locally on your machine.

## References

- [Tinder](https://tinder.com/) for research of dating profile parameters
- [OpenAI](https://platform.openai.com/) API

## Setup and Usage

### Software Requirements

- Python > 3.10
- [OpenAI API key](https://platform.openai.com/)

### Installation

1. Clone this repository:

```bash
git clone https://github.com/jonathanlawhh/dating-profile-optimizer
```

2. Install required libraries:

```bash
pip install -R requirements.txt
```

### Usage

1. Setup the `.env` with required information from `.env-sample`

2. Run the script.

```bash
python main.py
```

`.env` parameters:

| ENV NAME            | Accepted values    | Description                                  |
|---------------------|--------------------|----------------------------------------------|
| X_AUTH_TOKEN        | string             | Auth token from Tinder API                   |
| TINDER_API_ENDPOINT | https://xxx.com/v2 | Required. Tinder API Endpoint.               |
| OPENAI_API_KEY      | string             | Required. API Key from Open AI.              |
| OPENAI_MODEL        | gpt-4o-mini        | Model to use                                 |
| FLAG_DEVELOPMENT    | "TRUE" / "FALSE"   | Enable development feature                   |
| FLAG_USE_LOCAL_DATA | "TRUE" / "FALSE"   | Enable loading from JSON instead of live API |
| FLAG_DATA_GATHERING | "TRUE" / "FALSE"   | Enable data gathering mode                   |

## Closing thoughts

- LLM has come a long way that generates suggestions that are convincing
- Occasionally the LLM will hallucinate some information, perhaps better dev prompt required.