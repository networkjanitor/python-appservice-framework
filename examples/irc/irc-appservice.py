import asyncio

import bottom

from appservice_framework import AppService

loop = asyncio.get_event_loop()
loop.set_debug(True)


room = "#test01"

apps = AppService("http://localhost:8008",
                  "localhost",
                  "wfghWEGh3wgWHEf3478sHFWE",
                  "@irc_.*",
                  "#irc_.*",
                  "sqlite:///:memory:", loop=loop)

@apps.service_connect
async def connect_irc(apps, serviceid, auth_token):
    print("Connecting to IRC...")

    conn = bottom.Client("localhost", 6667, ssl=False, loop=loop)
    await conn.connect()

    conn.send("NICK", nick="matrix")
    conn.send("USER", user="matrix", realname="apps")

    # Temp join for testing
    conn.send('JOIN', channel=room)

    # Tempt send for testing
    conn.send('PRIVMSG', target=room, message="Hello")

    return conn


@apps.matrix_recieve_message
async def recieve_message(apps, auth_user, room, content):
    """
    """
    print("##", auth_user, room, content)
    conn = await apps.get_connection(wait_for_connect=False)
    conn.send('PRIVMSG', target=room.serviceid, message=content['body'])


user1 = apps.add_authenticated_user("@admin:localhost", "matrix", "")

# Use a context manager to ensure clean shutdown.
with apps.run() as run_forever:
    room = loop.run_until_complete(apps.create_linked_room(user1, f"#irc_{room}:localhost", room))
    conn = apps.get_connection(wait_for_connect=True)

    @conn.on("PRIVMSG")
    async def recieve_message(**kwargs):
        userid = kwargs['nick']
        roomid = kwargs['target']
        print(roomid)
        message = kwargs['message']
        print(message, roomid, userid)
        user = await apps.create_matrix_user(userid)
        await apps.add_user_to_room(user.matrixid, f"#irc_{roomid}:localhost")
        await apps.relay_service_message(userid, roomid, message, None)


    run_forever()
