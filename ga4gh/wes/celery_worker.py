from ga4gh.wes import celery
from ga4gh.wes.wesnake import create_connexion_app
from ga4gh.wes.celery_utils import init_celery

app, swagger = create_connexion_app()
init_celery(celery, app.app)
