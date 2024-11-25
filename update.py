from logging import FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info
from os import path as ospath, environ, remove
from shutil import copyfile
from subprocess import run as srun
from dotenv import load_dotenv
from pymongo import MongoClient

# Clear log file if it exists
if ospath.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

# Setup logging
basicConfig(format="[%(asctime)s] [%(levelname)s] - %(message)s",
            datefmt="%d-%b-%y %I:%M:%S %p",
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)

# Backup config.env before running the script
if ospath.exists('config.env'):
    log_info("Backing up config.env")
    copyfile('config.env', 'config.env.bak')

# Load environment variables
load_dotenv('config.env', override=True)

try:
    # Safety check for a specific variable
    if bool(environ.get('_____REMOVE_THIS_LINE_____')):
        log_error('The README.md file there to be read! Exiting now!')
        exit()
except:
    pass

# Retrieve environment variables
BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

DATABASE_URI = environ.get('DATABASE_URI', '')
if len(DATABASE_URI) == 0:
    DATABASE_URL = None

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
    UPSTREAM_REPO = None

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'master'

# Handle upstream repository updates
if UPSTREAM_REPO is not None:
    if ospath.exists('.git'):
        log_info("Removing existing .git directory")
        srun(["rm", "-rf", ".git"])

    update = srun([f"git init -q \
                     && git config --global user.email doc.adhikari@gmail.com \
                     && git config --global user.name weebzone \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)

    repo = UPSTREAM_REPO.split('/')
    UPSTREAM_REPO = f"https://github.com/{repo[-2]}/{repo[-1]}"
    if update.returncode == 0:
        log_info('Successfully updated with latest commits !!')
    else:
        log_error('Something went Wrong! Retry or Ask Support!')
    log_info(f'UPSTREAM_REPO: {UPSTREAM_REPO} | UPSTREAM_BRANCH: {UPSTREAM_BRANCH}')

# Restore config.env after running the script
if ospath.exists('config.env.bak'):
    log_info("Restoring config.env from backup")
    copyfile('config.env.bak', 'config.env')
    log_info("config.env restored successfully")
