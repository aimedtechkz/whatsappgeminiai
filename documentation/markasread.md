POST
Отметить сообщение прочитанным
https://wappi.pro/api/sync/message/mark/read?profile_id={{profile_id}}&mark_all=true
Метод позволяет отметить сообщение прочитанным.

HEADERS
Authorization
{{Token}}

PARAMS
profile_id
{{profile_id}}

Обязательный параметр. Можно получить в личном кабинете на странице конкретного профиля.

mark_all
true

Необязательный параметр. Значения true или false. Если true, то помечает все непрочитанные сообщения в чате прочитанными. Если не указывать, то по умолчанию стоит значение false.

Body
raw (json)
json
{
    "message_id": "3EB04E6C3BF173879610C0"
}
Example Request
Отметить сообщение прочитанным
curl
curl --location -g 'https://wappi.pro/api/sync/message/mark/read?profile_id={{profile_id}}' \
--header 'Authorization: {{Token}}' \
--data '{
    "message_id": "3EB04E6C3BF173879610C0"
}'
200 OK
Example Response
Body
Headers (5)
json
{
  "status": "done",
  "timestamp": 1683969533,
  "time": "2023-05-13T12:18:53+03:00",
  "uuid": "71ad40e9-b023"
}