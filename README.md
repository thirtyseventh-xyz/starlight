this serves everything for sparkle!

---

dev stuff: to get started, run `uv sync` to get the environment, and then make a .env file with equivalent contents to 
prod.env (this doesnt exist yet im too lazy, idk look at the code and figure it out). you at least need the database 
connection. after you configure env, run `alembic upgrade head` to setup your postgres database.