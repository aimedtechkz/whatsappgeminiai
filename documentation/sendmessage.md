POST
Отправить текстовое сообщение
https://wappi.pro/api/sync/message/send?profile_id={{profile_id}}
Отправка текстового сообщения.

HEADERS
Authorization
{{Token}}

PARAMS
profile_id
{{profile_id}}

Обязательный параметр. Можно получить в личном кабинете на странице конкретного профиля.

Body
raw (json)
json
{
    "body":"Тестовое сообщение",
    "recipient":"79115576362"
}
Example Request
Отправка сообщения
curl
curl --location -g 'https://{{url}}/api/sync/message/send?profile_id={{profile_id}}' \
--header 'Authorization: {{Token}}' \
--data '{
    "body":"Тестовое сообщение",
    "recipient":"79115576367"
}'
200 OK
Example Response
Body
Headers (5)
json
{
  "status": "done",
  "timestamp": 1679823696,
  "time": "2023-03-26T12:41:36+03:00",
  "message_id": "3EB0128AE55B5D222DD0",
  "task_id": "57411bfb-8f19-4d19-b6c1-2457b5164fd2"
}