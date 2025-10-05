POST
Ответить на сообщение
https://wappi.pro/api/sync/message/reply?profile_id={{profile_id}}
Ответить на сообщение. Чтобы отправить файл необходимо в body добавить поле url файла. Если не добавлять поле url, то будет отправлен просто текст.

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
    "body": "тестовый ответ на сообщение",
    "message_id": "3EB0F4D080603C3C0C0A",
    "url": "https://freetestdata.com/wp-content/uploads/2022/02/Free_Test_Data_117KB_JPG.jpg"
}
Example Request
Ответить на сообщение
curl
curl --location -g 'https://{{url}}/api/sync/message/reply?profile_id={{profile_id}}' \
--header 'Authorization: {{Token}}' \
--data '{
    "body": "тестовый ответ на сообщение",
    "message_id": "3EB0F4D080603C3C0C0A"
}'
200 OK
Example Response
Body
Headers (5)
json
{
  "status": "done",
  "timestamp": 1679824453,
  "time": "2023-03-26T12:54:13+03:00",
  "message_id": "3EB0F2ECAAC3AF1D6219",
  "task_id": "a71af6ad-0c6c-41bf-abc1-4e8a47eb665d"
}