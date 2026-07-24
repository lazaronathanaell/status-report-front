# General Vision

This branch contains all the data API functionalities, ready to be locally tested. So it is useful for API-level tests without integrating with the rest of the application.

# How to run

1. Ensure you have a .env file with the necessary constants:


```
# PostgreSQL
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_database_name
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Ollama / LLM
OLLAMA_URL=http://your_ollama_host:11434/api/generate
MODEL=your_model_name

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# SQLAlchemy / App DB URL
DATABASE_URL=postgresql://your_postgres_user:your_postgres_password@db:5432/your_database_name

# Celery
CELERY_BROKER_URL=redis://redis:6379/0

# JWT / Auth
ALGORITHM=HS256
SECRET_KEY=your_jwt_secret_key

ACCESS_TOKEN_EXPIRE_MINUTES=30

MODEL_GENERO=/app/modules/verificar_genero/models/modelo_genero.pkl
```

2. Install the packages.


``` bash
cd app
pip install -r requirements.txt
```

3. Execute docker.

For the first time:

```bash
docker compose --profile setup up --build
```

After the first build, you may just use:

```bash
docker compose up
```

4. Test the API

The API endpoints are available at http://localhost:8000/docs

# Client example for tests

With the dataset available from the project, a index file was filled to make the tests easier. At the moment, 9 teachers have all login information filled in this file: pipeline_question_answering\Scripts\index.json

Then you might run this script to generate the docs for each person(ensure the original pdfs are pasted in the proper directory):

``` bash
cd pipeline_question_answering\Scripts
python generate_separate_docs.py
```

Finally, run the client:

```bash
python automatic_login.py
```

With this, the e-mail login for each professor will follow the pattern {NUP}@example.com.
The best way to see the validation results is by GET http://localhost:8000/pdfs/structured-all


