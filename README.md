# PanQPlex

Uploads videos en mass to youtube, throttles uploads to fit in youtube's terms, helps to manage video metadata, upload history, and syncronization between local videos and youtube's uploaded items.

## Usage

Available flag, commands etc are in development yet.

Run `pqp -h` for more information on the current state.

Currently the flow should look something like this:

```
# Go to the folder with the videos to upload
cd my-movies;

# Get to know pqp's current interface
pqp -h;

# Do the OAuth thing, probably will fail
pqp list-channels;

# OAuth again, should work;
pqp list-channels;

# List your account's channels
pqp list-channels;

# Scan PWD for uploadable videos
pqp scan;

# Start throttled upload loop
pqp start;

# wait...
# done \o/
```

## Installation

Clone this repo:

```
git clone "git@github.com:annibal/PanQPlex.git" PanQPlex;
cd PanQPlex;
```;

Ensure you have `python3` and `pip` installed:

[Install Python on Unix](https://docs.python-guide.org/starting/install3/linux/) | [Install PIP without ROOT](https://askubuntu.com/questions/363300/how-to-install-pip-python-to-user-without-root-access) | [Python3 Windows Releases](https://www.python.org/downloads/source/)

then, refer to whick kind of installation (user or developer) fits your goal (upload videos or contribute):


### Run in Development Mode

```
./install.sh;

source .venv/bin/activate
```

If this works, you will see a "(.venv)" prefixed to your shell.

### Install as an unix package

wip

### Update as an unix package

wip