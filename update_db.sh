#!/bin/bash

# Apply database migrations
echo "Make migrations"
python manage.py makemigrations --settings $1

# Apply database migrations
echo "Apply migrations"
python manage.py migrate --settings $1

# Create groups
echo "Create Groups"
python manage.py create_groups --settings $1

# Create services and trade bodies
echo "Create services and trade bodies"
python manage.py create_services_and_trade_bodies --settings $1

# Create static files
echo "Create static files"
python manage.py collectstatic --settings $1
