# Audioguide Rental

This project provides a Django REST API and a React frontend for managing audioguide rentals.

## Requirements

- Python 3.8+
- Node.js 18+

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the backend (from the `backend` directory):

```bash
python manage.py migrate
python manage.py runserver
```

The frontend uses Vite. From the `frontend` folder run:

```bash
npm install
npm run dev
```

## Running tests

Inside the `backend` folder execute:

```bash
python manage.py test
```


## Deployment to Railway

1. Sign in to [Railway](https://railway.app/) and create a new project.
2. Add a **PostgreSQL** database plugin to the project and note the `DATABASE_URL` it provides.
3. From the project dashboard, create a new service from this repository.
4. Set the following environment variables in Railway:
   - `DJANGO_SECRET_KEY` – a unique secret key for Django
   - `DJANGO_DEBUG` – set to `False`
   - `DATABASE_URL` – the value from the PostgreSQL plugin
5. In the service settings, set the build command to `pip install -r requirements.txt` and the start command to `python backend/manage.py migrate && python backend/manage.py runserver 0.0.0.0:8000`.
6. Deploy the service. Railway will provide a public URL for your Django API.
7. For the React frontend, either create a separate service that runs `npm install && npm run build` and serves the `dist` folder, or configure a static hosting provider.
