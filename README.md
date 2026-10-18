# Trip Planner Agent

A conversational travel-planning agent built with LangChain and LangGraph. The
agent can research weather, attractions, restaurants, ticketed events, and
transit guidance, then refine the plan over multiple turns and extract the
conversation into a structured itinerary.

## Features

- Conversational trip planning with short-term memory.
- Weather forecasts from Open-Meteo, including city disambiguation and the
  16-day forecast limit.
- Web-search recommendations for attractions, restaurants, and transit
  guidance through Tavily.
- Ticketmaster event searches with local-date filtering, venue information,
  source links, and explicit handling for unpublished prices.
- Source URLs for recommendations.
- A typed itinerary containing days, activities, costs, and unresolved
  questions.
- Terminal chat mode and a Gradio web interface.

The agent is intentionally conservative about information that the tools cannot
confirm. Search snippets do not provide reliable opening hours or current
prices, transit search does not provide exact journey times, and a missing
Ticketmaster price is not treated as free.

## Project structure

```text
trip_planner/
├── agent/
│   ├── agent.py       # Model, tools, memory, and terminal entry point
│   ├── itinerary.py   # Pydantic itinerary models and extraction
│   ├── prompts.py     # Agent system prompt
│   └── tools.py       # Weather, search, events, and transit tools
├── agentui.py         # Streaming Gradio chat UI
├── app.py             # Web application entry point
└── requirements.txt   # Python dependencies
```

## Requirements

- Python 3.10 or newer
- A Google Gemini API key, or a compatible model configuration
- A Tavily API key
- A Ticketmaster Discovery API key

Open-Meteo weather and geocoding requests do not require an API key.

Create a `.env` file in `trip_planner/` with:

```dotenv
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
TICKETMASTER_API_KEY=your_ticketmaster_api_key
```

Never commit `.env` or publish API keys. The repository should remain private
when it is used for course submission.

## Installation

From the repository root:

```bash
cd trip_planner
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the application

### Terminal mode

```bash
cd trip_planner
python -m agent.agent
```

Describe a trip, refine it in the same conversation, and type `quit` or
`exit` to stop. The terminal session then prints the structured itinerary.

### Web interface

```bash
cd trip_planner
python app.py
```

Open <http://127.0.0.1:7860>. The web UI streams tool calls and results while
the agent is working. After chatting, select **Build itinerary from this
conversation** to display the structured JSON output.

The application uses a stable LangGraph `thread_id` for each conversation, so
follow-up requests such as “make it rainy-day friendly” can update the existing
plan rather than starting over.

## Tool behavior and limitations

| Tool | Purpose | Important limitation |
| --- | --- | --- |
| `get_weather(city, date)` | Resolves a city and gets current or daily weather | Forecasts are available only for today and the next 15 days |
| `find_attractions(city, interest)` | Finds sights, museums, parks, and landmarks | Search snippets may not contain hours or prices |
| `find_restaurants(city, budget)` | Finds places to eat | Search snippets may not contain hours or current prices |
| `find_events(city, date, category)` | Finds Ticketmaster events, dates, venues, and links | Ticket prices are usually unavailable; results cover Ticketmaster events only |
| `get_transit_info(city)` | Finds general transit guidance | Does not provide exact timetables or journey durations |

The tools return evidence for the model to summarize. They should not be used
to invent opening hours, journey times, ticket prices, or seasonal forecasts.
In particular:

- An ambiguous city name must be confirmed before planning.
- A forecast outside the 16-day window is reported as unavailable.
- A missing price is represented as `unknown` or `price not published`, not
  `$0` or “free”.
- A quiet Ticketmaster result does not prove that a city has no events.

## Structured itinerary

The **Build itinerary** action extracts the conversation into an `Itinerary`
Pydantic model:

```json
{
  "City": "Boston",
  "Days": [
    {
      "Date": "2026-10-03",
      "Weather": "partly cloudy, 18°C / 11°C",
      "Activities": [
        {
          "time": "morning",
          "name": "Example activity",
          "kind": "sight",
          "cost": "unknown",
          "source": "https://example.com"
        }
      ]
    }
  ],
  "Unknowns": [
    "Opening hours were not confirmed by the available tools"
  ]
}
```

`Activity.cost` is deliberately a string. This allows the itinerary to preserve
“unknown”, “free” only when explicitly supported, or a price with its source.

## Suggested manual checks

Use the prompts in [`test_prompts.md`](./test_prompts.md) in order. They cover:

1. A basic one-day plan and tool selection.
2. Refining an existing plan using conversation memory.
3. A date beyond the weather forecast window.
4. Ambiguous locations such as Cambridge or Portland.
5. Unconfirmed museum opening hours.
6. Transit questions that ask for an exact duration.
7. A total-cost request when most prices are unknown.
8. Ticketmaster events, missing prices, unsupported categories, and exact
   local-date filtering.

The expected behavior is honesty about what the APIs actually returned, not a
plausible guess.

## Deploying to Render

Create a private GitHub repository and connect it to a Render **Web Service**.
Use these settings:

| Setting | Value |
| --- | --- |
| Root directory | `trip_planner` |
| Build command | `pip install -r requirements.txt` |
| Start command | `python app.py` |

Add `GOOGLE_API_KEY`, `TAVILY_API_KEY`, and `TICKETMASTER_API_KEY` as Render
environment variables. Do not put them in the repository. `app.py` listens on
`0.0.0.0` and uses Render’s `$PORT` value automatically.

After deployment, replace the placeholder at the top of this file with the
actual Render URL. The free Render tier may sleep after inactivity, so the
first request after a pause can take longer.

## References

- [LangChain documentation](https://python.langchain.com/)
- [Open-Meteo documentation](https://open-meteo.com/en/docs)
- [Tavily](https://tavily.com/)
- [Ticketmaster Discovery API](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/)
- [Gradio documentation](https://www.gradio.app/docs)
