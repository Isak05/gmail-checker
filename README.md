# Gmail Checker

Automatically polls the Gmail API to check for unread mail. Tested on Kubuntu 23.04 x86_64.

**_NOTE:_** This is just a basic prototype.

This project doesn't have a public google cloud app associated with it. To set up you need to create your own google cloud app. Enable the Gmail API in the app and add an OAuth client ID credential. Make sure to add yourself as a test user. Download this repository and create a file named `config.conf`. It should contain the following:
```
CLIENT_ID=
CLIENT_SECRET=
HOST=http://127.0.0.1
PORT=
AUDIO_FILE=
```
Paste the client id and secret you got from the OAuth credential on their respective lines. Put a free localhost port after `PORT=`. If you want a sound to play when you get the notification, put the sound file name after `AUDIO_FILE=`. Or else you can remove that line. The `autorun` script calls `run` every 5 minutes. And the `run` script reads and passes config.conf to `run.py`.

## TODO

* Use python libraries instead of relying on `notify-send` and `ffplay`.
* Compatability improvements.
* Shouldn't need to create own google cloud app.
* Don't hijack org.kde.konsole for sending notifications