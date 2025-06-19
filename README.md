Проект "Продуктовый помощник" Foodgram

[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=56C0C0&color=008080)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=56C0C0&color=008080)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat&logo=Django%20REST%20Framework&logoColor=56C0C0&color=008080)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat&logo=PostgreSQL&logoColor=56C0C0&color=008080)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/-Docker-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker-compose](https://img.shields.io/badge/-Docker%20compose-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker Hub](https://img.shields.io/badge/-Docker%20Hub-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/products/docker-hub)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat&logo=NGINX&logoColor=56C0C0&color=008080)](https://nginx.org/ru/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat&logo=GitHub%20actions&logoColor=56C0C0&color=008080)](https://github.com/features/actions)

# Описание проекта Foodgram

Foodgram —— сайт, на котором пользователи могут публиковать свои рецепты, 
подписываться на других авторов и добавлять в избранное их рецепты. 
Сервис «Список покупок» поможет пользователям создавать список ингредиентов, 
которые нужно купить, чтобы приготовить выбранные блюда.

# Документация

Документация для API

```url
    /api/docs/redoc.html
```

# Как запустить проект
🔧 Подготовка
Убедитесь, что на вашем сервере установлен Docker и Docker Compose :

```bash
sudo systemctl status docker
docker-compose --version
```

Если Docker не установлен, установите:

```bash
sudo apt install docker.io
```

Создайте папку проекта:
```bash
mkdir foodgram && cd foodgram
```

Скачайте файл docker-compose.production.yml в эту папку.

# Настройка переменных окружения
Создайте файл .env в корне проекта и заполните его по образцу Start example.env

# Запуск контейнеров
```bash
sudo docker compose -f docker-compose.production.yml up -d
```

# Выполнение миграций и сбор статики
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

# Загрузка начальных данных
Для первоначального наполнения базы тегами и ингредиентами выполните:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py data_loader
```

# Остановка проекта
```bash
sudo docker compose -f docker-compose.production.yml down
```

# Доступ к сайту
После запуска сайт будет доступен по адресам:

http://localhost:9000
http://127.0.0.1:9000
http://ваш_внешний_IP:9000

# Автор
Костюкович Владислав
Telegram: @kostyan_vd