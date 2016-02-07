# Toornament Bot
It's a Telegram Bot built upon [Toornament API](https://www.toornament.com), which helps Hearthstone tournament participants manage their own games by themselfs.

## Setup
The installation is lack of automation yet, sorry. First, you should have Hearthstone tournament created using https://www.toornament.com. You should conplete registration and have all participants accepted.

- Create AWS DynamoDB table and save it's name into `PARTICIPANTS_TABLE` environment variable. It will be used for linking participants with their Telegram accounts.
- Export your tournament participants as `CSV` file from https://www.toornament.com/admin/tournaments/
