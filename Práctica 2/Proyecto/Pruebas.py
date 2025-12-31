import requests
import time

URL = "https://localhost:8000/juego/nombre/H"  
VERIFY_SSL = False   

for i in range(20):  
    try:
        response = requests.get(URL, verify=VERIFY_SSL)
        print(f"[{i+1}] Status: {response.status_code}")

        try:
            print("Respuesta:", response.json())
        except:
            print("Respuesta no JSON")

    except Exception as e:
        print("Error:", e)

    time.sleep(0.2)  
