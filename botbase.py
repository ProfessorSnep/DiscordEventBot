import discord
import discord.ext.commands as commands
import json
import os
import datetime
import asyncio
import pytz

bot = commands.Bot(command_prefix="b.")

with open(os.path.join(os.path.dirname(__file__), "botkey"), "r") as botkey:
    BOT_KEY = botkey.read()

with open(os.path.join(os.path.dirname(__file__), "events.json"), "r") as botevents:
    BOT_EVENTS = json.loads(botevents.read())

with open(os.path.join(os.path.dirname(__file__), "channels.json"), "r") as botchannels:
    BOT_CHANNELS = json.loads(botchannels.read())

_id = 0
EVENTS = []
ACTIVE_EVENTS = []


class Event:
    def __init__(self, name, datestring, asset, timezone, event_type):
        date = datestring.split("/")
        global _id
        self.id = _id
        _id += 1
        self.day = int(date[0])
        self.mon = int(date[1])
        self.type = event_type
        self.asset = asset
        self.name = name
        self.timezone = pytz.timezone(BOT_EVENTS['timezones'][timezone])

    @staticmethod
    def get_by_id(id):
        return next(e for e in EVENTS if e.id == id)


for k, v in BOT_EVENTS['events'].items():
    for e in v:
        EVENTS.append(Event(e['name'], e['date'],
                            e['asset'], e['timezone'], k))

TIMEZONES = BOT_EVENTS['timezones']


async def announce_event_start(event):
    print("START", event.name)
    channels = BOT_CHANNELS['announcement']
    for cid in channels:
        channel = bot.get_channel(cid)
        await channel.send(f"Event Start: {event.name}")


async def announce_event_end(event):
    print("END", event.name)


async def check_task():
    global ACTIVE_EVENTS
    initial_startup = True  # don't announce events have started on the first run of the loop
    _daycount = 1
    while not bot.is_closed():
        current_active = []  # the active events in this run of the loop
        print(_daycount)

        # find which events are active
        for ev in EVENTS:
            date = datetime.datetime.now(tz=ev.timezone).date()
            if ev.mon == date.month and ev.day == _daycount:
                # event is active

                current_active.append(ev.id)
                if ev.id not in ACTIVE_EVENTS:
                    # event has just started

                    ACTIVE_EVENTS.append(ev.id)
                    if not initial_startup:
                        await announce_event_start(ev)

        # find events that just ended
        for eid in ACTIVE_EVENTS:
            if eid not in current_active:
                # event has just ended

                ACTIVE_EVENTS.remove(eid)
                if not initial_startup:
                    ev = Event.get_by_id(eid)
                    await announce_event_end(ev)

        print(ACTIVE_EVENTS)
        _daycount %= 30
        _daycount += 1

        initial_startup = False
        await asyncio.sleep(1)


@bot.event
async def on_ready():
    print("Ready!")

if __name__ == "__main__":
    bot.loop.create_task(check_task())
    bot.run(BOT_KEY)
