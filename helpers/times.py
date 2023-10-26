import datetime

local_tz = datetime.timezone(offset=datetime.timedelta(hours=1.0), name="BST")
reset_time = datetime.time(hour=3, minute=0, tzinfo=local_tz) ### INVASION DB RESET TIME BST ###

def right_now(fmt=None):
    if fmt == "full":
        return datetime.datetime.now().strftime('%d/%m/%Y - %H:%M:%S')
    elif fmt == "HM": 
        return datetime.datetime.now().strftime('%H:%M')
    elif fmt == "ping check":
        return datetime.datetime.now() + datetime.timedelta(hours=1)
    else:
        return datetime.datetime.now()

def vote_expiration():
    now = datetime.datetime.now()
    expiration = now.replace(day=now.day+1, hour=3, minute=0, second=0, microsecond=0)
    return expiration