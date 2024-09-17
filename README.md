### О проекте
Foodgram - сервис, который позволяет пользователям публиковать и редактировать свои рецепты, добавлять рецепты в избранное, подписываться на других авторов, формировать из рецептов список покупок и скачивать его. 


### Используемые технологии
* Python 3.9
* Django 3.2
* Django Rest Framework 3.12.4
* Djoser 2.1
* Docker
* PostgreSQL

### Как запустить проект на сервере
1. Скопируйте из репозитория файл docker-compose.production.yml
2. В этой же директории создайте .env файл по примеру .env.example
3. Выполните команду:
```bash
sudo docker compose -f docker-compose.production.yml up -d
```
4. Для создания суперпользователя, выполните команду:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

### Разделы проекта
**Главная** - /recipes/ \
**API** - /api/ \
**Админ зона** - /admin/

### Примеры запросов
1. Получение списка рецептов: \
   **GET** `/api/recipes/` \
   RESPONSE
   ```json
   {
     "count": 123,
     "next": "/api/recipes/?page=2",
     "previous": "/api/recipes/?page=1",
     "results": [
       {
         "id": 0,
         "tags": [
           {
             "id": 0,
             "name": "Завтрак",
             "slug": "breakfast"
           }
         ],
         "author": {
           "email": "ivan@ivan.com",
           "id": 0,
           "username": "ivanivan",
           "first_name": "Ivan",
           "last_name": "Ivanov",
           "is_subscribed": false
         },
         "ingredients": [
           {
             "id": 0,
             "name": "Курица",
             "measurement_unit": "г",
             "amount": 100
           }
         ],
         "is_favorited": false,
         "is_in_shopping_cart": false,
         "name": "string",
         "image": "/media/recipes/images/image.jpeg",
         "text": "string",
         "cooking_time": 10
       }
     ]
   }
   ```
3. Регистрация пользователя: \
   **POST** `/api/users/` \
   REQUEST
   ```json
   {
     "email": "ivan@ivan.com",
     "username": "ivanivan",
     "first_name": "Ivan",
     "last_name": "Ivanov",
     "password": "super_password1"
   }
   ```
   RESPONSE
   ```json
   {
   "email": "ivan@ivan.com",
   "id": 1,
   "username": "ivanivan",
   "first_name": "Ivan",
   "last_name": "Ivanonv"
   }
   ```
4. Подписаться на пользователя: \
   **POST** `/api/users/{id}/subscribe/` \
   RESPONSE
   ```json
   {
     "email": "ivan@ivan.com",
     "id": 1,
     "username": "ivanivan",
     "first_name": "Ivan",
     "last_name": "Ivanov",
     "is_subscribed": true,
     "recipes": [
       {
         "id": 0,
         "name": "string",
         "image": "/media/recipes/images/image.jpeg",
         "cooking_time": 10
       }
     ],
     "recipes_count": 1
   }
   ```

### Об авторе
Foodgram - дипломный проект курса Backend-разработки Яндекс.Практикум. Автор - Денис Хамцев.
https://github.com/Khamtsev/
