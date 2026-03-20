im too lazy to write a proper readme but starlight is the backend for sparkle, handling oauth and all the other stuff a backend does
for dev, to get python to read the environment variables, you have to uncomment the `from dotenv import load_dotenv` and `load_dotenv()` lines because python on docker is stupid. comment these lines out when you commit your code, or else ill do something (idk what)
