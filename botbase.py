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
EVENTS = set()
ACTIVE_EVENTS = set()


class EventDate:
    def __init__(self, datestring):
        self.datestring = datestring
        date, time = datestring.split(" ")
        day, mon = date.split("/")
        hour, minute = time.split(":")
        self.day = int(day)
        self.mon = int(mon)
        self.hour = int(hour)
        self.minute = int(minute)

    def to_datetime(self, tzinfo, year):
        date = datetime.datetime.strptime(self.datestring, "%d/%m %H:%M:%S")
        date = date.replace(year=year, tzinfo=tzinfo)
        return date


class Event:
    def __init__(self, name, startdate, enddate, asset, timezone, event_type):
        global _id
        self.id = _id
        _id += 1
        self.start_date = startdate
        self.end_date = enddate
        self.type = event_type
        self.asset = asset
        self.name = name
        self.timezone = pytz.timezone(BOT_EVENTS['timezones'][timezone])

    def is_active(self, current_time=None):
        if not current_time:
            current_time = datetime.datetime.now(tz=self.timezone)
        start = self.start_date.to_datetime(current_time.tzinfo, current_time.year)
        end = self.end_date.to_datetime(current_time.tzinfo, current_time.year)
        print(start, end, current_time)
        if (start < end):
            # event does not wrap a year
            return current_time >= start and current_time < end
        else:
            # event wraps a year
            return start >= current_time or end < current_time

    @staticmethod
    def get_by_id(id):
        return next(e for e in EVENTS if e.id == id)


for k, v in BOT_EVENTS['events'].items():
    for e in v:
        start = EventDate(e['start'])
        end = EventDate(e['end'])
        EVENTS.add(Event(e['name'], start, end,
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
        current_active = set()  # the active events in this run of the loop
        print(_daycount)

        to_announce_start = []
        to_announce_end = []

        # find which events are active
        for ev in EVENTS:
            date = datetime.datetime.now(tz=ev.timezone)
            #date = date.replace(day=_daycount)
            if ev.is_active(date):
                # event is active

                current_active.add(ev.id)
                if ev.id not in ACTIVE_EVENTS:
                    # event has just started

                    ACTIVE_EVENTS.add(ev.id)
                    to_announce_start.append(ev)

        # find events that just ended
        for eid in set(ACTIVE_EVENTS):
            if eid not in current_active:
                # event has just ended

                ACTIVE_EVENTS.remove(eid)
                ev = Event.get_by_id(eid)
                to_announce_end.append(ev)

        if not initial_startup:
            tasks = [announce_event_start(
                ev) for ev in to_announce_start] + [announce_event_end(ev) for ev in to_announce_end]
            asyncio.gather(*tasks)

        print(ACTIVE_EVENTS)
        #_daycount %= 30
        #_daycount += 1

        initial_startup = False
        await asyncio.sleep(1)


@bot.event
async def on_ready():
    print("Ready!")

if __name__ == "__main__":
    bot.loop.create_task(check_task())
    bot.run(BOT_KEY)
