this serves everything for sparkle!

---

dev stuff: to get started, run `uv sync` to get the environment, then copy `example.env` to `.env` and fill it out. the 
database connection, secret key, and encryption key are critical for the site to work at all, leaving the rest will only 
break small parts. after you configure env, run `alembic upgrade head` to set up your postgres database.

to make sure the frontend is present (its pulled from a git submodule), run `git submodule update --init --recursive`

if you need to run the docker image ~~just use your editor's dockerfile tester~~, build it using `docker build -t starlight-dev .`, 
and then run it with `docker run --name personal-website --network=host --env-file .env personal-website` 