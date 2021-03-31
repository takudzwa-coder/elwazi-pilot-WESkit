import weskit
import os

if __name__ == "__main__":
    current_app = weskit.create_celery(os.environ["BROKER_URL"],
                                       os.environ["RESULT_BACKEND"])
