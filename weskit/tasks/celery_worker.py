import weskit
import os

current_app = weskit.create_celery(os.environ["BROKER_URL"],
                                   os.environ["RESULT_BACKEND"])
