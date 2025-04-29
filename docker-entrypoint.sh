#!/bin/bash

# Apply database migrations
echo "Make migration for accounts"
python manage.py makemigrations accounts --settings pstf.settings.dev

# Make migrations
echo "Make migrations for registration"
python manage.py makemigrations registration --settings pstf.settings.dev

# Make migrations
echo "Make migrations for upload"
python manage.py makemigrations upload --settings pstf.settings.dev

# Make migrations
echo "Make migrations for data"
python manage.py makemigrations data --settings pstf.settings.dev

# Apply database migrations
echo "Apply migrations"
python manage.py migrate --settings pstf.settings.dev

# Create groups
echo "Create Groups"
python manage.py create_groups --settings pstf.settings.dev

# Create services and trade bodies
echo "Create services and trade bodies"
python manage.py create_services_and_trade_bodies --settings pstf.settings.dev

# Load test data
# echo "Load test data"
# python manage.py load_test_data --settings pstf.settings.base

# Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000 --settings pstf.settings.dev