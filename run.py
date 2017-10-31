from app import app
import os


config_name = os.getenv('APP_SETTINGS')

if __name__ == '__main__':
    app.run()
