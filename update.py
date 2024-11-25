from logging import FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info
from os import path as ospath, environ, remove
from shutil import copyfile
from subprocess import run as srun
from dotenv import load_dotenv
from pymongo import MongoClient


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
                     && git config --global user.email doc.ironman966232@gmail.com \
                     && git config --global user.name Ironman966232 \
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
