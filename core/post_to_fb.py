import requests
data = {"message": "Anotherly Posted From Python! \n Follow This link: https://breakernews.net", "link":"https://breakernews.net", "access_token":"EAALMC9xx9ToBAF2Dw4NSIZAroJ3kLYOvHqPsropOH7TBBINiVeHFLBTGwBl6YSf8aTxNDqxPCp1fPr74do9r12q2qZCHylVe4OZCOXCgypQqx6hj7eWYnXESzf64fXV0c6vNktRGXcDUUpq0udXpbttDJZAUYUEnt85707LH1wZDZD"}
response = requests.post(url="https://graph.facebook.com/105840371657222/feed", data=data)
print(response.json())
# response = requests.get("http://127.0.0.1:5000/api/v1/news?key=TsMsvGDMLBbp-kKjSVqRiONSfja5Ocpf&lang=ur")
# print(response.json())