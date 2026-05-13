import time
import requests

start = time.time()
res = requests.get("http://127.0.0.1:8000/api/clips")
print(f"API /api/clips took {time.time() - start:.3f}s. Status: {res.status_code}")
