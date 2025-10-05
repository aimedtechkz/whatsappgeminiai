GET
Получить сообщения из чата
https://wappi.pro/api/sync/messages/get?profile_id={{profile_id}}&chat_id=79115576369&limit=1&date=2019-11-02T23:16:58&offset=0&mark_all=true&order=desc
Получение сообщений из конкретного чата.

HEADERS
Authorization
{{Token}}

PARAMS
profile_id
{{profile_id}}

Обязательный параметр. Можно получить в личном кабинете на странице конкретного профиля.

chat_id
79115576369

Обязательный параметр. ID чата из списка сообщений.

Примеры:

13475634251@c.us - id чата

79115556677 - номер телефона чата

134756342511567456345@g.us - id чата группы

limit
1

Необязательный параметр. Количество сообщений для получения. Если не указывать, то по умолчанию установлено значение 400.

date
2019-11-02T23:16:58

Необязательный параметр. Дата, с которой вывести список сообщений. Формат YYYY-mm-ddTHH:MM:ss (например 2023-12-31T12:00:00).

offset
0

Необязательный параметр. От какого по счету элемента вывести список сообщений, где 0 это самое новое сообщение. Если не указывать, то по умолчанию установлено значение 0.

mark_all
true

Необязательный параметр. Значения true или false. Если true, то помечает все непрочитанные сообщения в чате прочитанными. Если не указывать, то по умолчанию стоит значение false. Работает только для личных чатов, для групп не работает.

order
desc

Необязательный параметр. Значения desc или asc. Если desc - сортирует от нового к старым, если asc - от старого к новым. Если не указывать, то по умолчанию стоит desc

Example Request
Получить сообщения из чата
View More
curl
curl --location -g 'https://wappi.pro/api/sync/messages/get?profile_id={{profile_id}}&chat_id=79115576367&limit=1&date=2019-11-02T23%3A16%3A58&offset=0&order=desc' \
--header 'Authorization: {{Token}}'
200 OK
Example Response
Body
Headers (6)
View More
json
{
  "status": "done",
  "timestamp": 1720788635,
  "time": "2024-07-12T15:50:35+03:00",
  "messages": [
    {
      "id": "3EB0B62774646FC3959E87",
      "type": "chat",
      "from": "79602041980@c.us",
      "to": "79115576367@c.us",
      "fromMe": true,
      "senderName": "Ми",
      "time": 1720780615,
      "body": "Test message from wappi.pro",
      "stanzaId": "",
      "chatId": "79115576367@c.us",
      "isForwarded": false,
      "isReply": false,
      "caption": "",
      "isRead": false,
      "delivery_status": "delivered",
      "s3Info": {},
      "poll_votes": null,
      "poll_options": null,
      "poll_select_count": 0,
      "isEdited": false,
      "isFromAPI": false,
      "isDeleted": false,
      "isPinned": false
    }
  ],
  "total_count": 1406,
  "uuid": "6d154f68-71ec"
}