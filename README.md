# Video Generation

This project generates short videos based on a single prompt. 

It uses the following technologies:

* OpenAI for generating the script and the images.
* Murf AI for generating the voiceover
* MoviePy for creating the final video.

## Environment variables

Create a `.env` file in the root of the project and add the following variables:

* `OPENAI_API_KEY`
* `MURF_API_KEY` (Get your API key from [Murf AI API's page](https://murf.ai/api))

## Running the project

```bash
uv init
uv run python main.py
```

