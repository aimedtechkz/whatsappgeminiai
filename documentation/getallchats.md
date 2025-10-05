POST
Получить список чатов
https://wappi.pro/api/sync/chats/get?profile_id={{profile_id}}&limit=10&show_all=false&offset=0
Получение списка всех чатов в подключенном аккаунте Whatsapp.

В body можно передать массив "filter", в элементах которого можно использовать регулярные выражения. Вы можете оставить body пустым, если не хотите использовать фильтр.

HEADERS
Authorization
{{Token}}

PARAMS
profile_id
{{profile_id}}

limit
10

show_all
false

offset
0


Example Request
Получить список чатов
curl
curl --location -g 'https://{{url}}/api/sync/chats/get?profile_id={{profile_id}}&limit=2' \
--header 'Authorization: {{Token}}'
200 OK
Example Response
Body
Headers (5)
View More
json
{
  "status": "done",
  "timestamp": 1679494397,
  "time": "2023-03-22T17:13:17.957011925+03:00", 
  "dialogs": [
    {
      "id": "79115576367@c.us",
      "contact": {
        "Found": true,
        "FirstName": "Макс Моряк ⚓",
        "FullName": "Макс Моряк ⚓",
        "PushName": "Flood",
        "BusinessName": ""
      },
      "chat": {
        "VerifiedName": null,
        "Status": "‎В кино",
        "Pict