#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Prompt for superuser creation
echo "Would you like to create a superuser now? (y/n)"
read create_superuser

if [ "$create_superuser" == "y" ]; then
    python manage.py createsuperuser
fi
