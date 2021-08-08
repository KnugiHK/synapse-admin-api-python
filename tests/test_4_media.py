"""MIT License

Copyright (c) 2021 Knugi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import glob
import httpx
import mimetypes
import os
import pytest
from synapse_admin import Media, Room
from synapse_admin.base import HTTPConnection, SynapseException, Utility
from uuid import uuid4


with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
media_handler = Media(*conn)
test1_conn = HTTPConnection(
    "http://",
    "localhost",
    8008,
    {"Authorization": f"Bearer {user_access_token}"}
)
test1_conn.method_map["HEAD"] = test1_conn.conn.head

media_id = []
reference_room = Room(*conn).lists()[0]["room_id"]


def query_media(mediaid):
    mediaid = media_handler.extract_media_id(mediaid)
    return test1_conn.request(
        "HEAD",
        f"/_matrix/media/r0/download/localhost/{mediaid}"
    )


def get_testing_media():
    path = os.path.dirname(os.path.realpath(__file__))
    search = os.path.join(path, "media/[!README.md]*")
    return sorted(glob.glob(search))


def upload_media():
    global media_id
    http_client = httpx.Client()
    endpoint = "http://localhost:8008/_matrix/media/r0/upload"
    testing_media = get_testing_media()
    test1_media = testing_media[:2]
    admin1_media = testing_media[2:]
    for media in testing_media:
        if media in test1_media:
            token = user_access_token
        elif media in admin1_media:
            token = admin_access_token
        with open(media, "rb") as f:
            resp = http_client.post(
                f"{endpoint}?filename={os.path.basename(media)}",
                content=f.read(),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": mimetypes.guess_type(media)[0],
                    "Content-Length": f"{os.path.getsize(media)}"
                }
            )
        if resp.status_code == 200:
            media_id.append(resp.json()["content_uri"])
        else:
            raise RuntimeError(resp.json())

    return True


def post_media():
    path = os.path.dirname(os.path.realpath(__file__))
    for index, media in enumerate(media_id[:2]):
        filename = f"image{index + 1}.jpg"
        resp = test1_conn.request(
            "PUT",
            f"/_matrix/client/r0/rooms/{reference_room}"
            f"/send/m.room.message/{uuid4()}",
            {
                "body": filename,
                "msgtype": "m.image",
                "url": media,
                "info": {
                    "h": 1280,
                    "w": 1920,
                    "mimetype": "image/jpeg",
                    "thumbnail_info": None,
                    "thumbnail_url": None,
                    "size": os.path.getsize(
                        os.path.join(
                            path,
                            "media",
                            filename
                        )
                     )
                }
            }
        )
        if "event_id" not in resp.json():
            raise RuntimeError("Posting of media failed")
    return True


def test_media_statistics():
    """TODO: from_ts, until_ts"""
    assert upload_media()
    stats = media_handler.statistics()
    assert stats[0]["user_id"] == "@test1:localhost"
    assert stats[0]["media_count"] == 2
    assert stats[0]["media_length"] == 1418007
    assert stats[1]["user_id"] == "@admin1:localhost"
    assert stats[1]["media_count"] == 3
    assert stats[1]["media_length"] == 10761727

    stats = media_handler.statistics(
        limit=1,
        orderby="displayname",
        forward=False
    )
    assert stats[0]["user_id"] == "@test1:localhost"
    assert stats.total == 2 and stats.next == 1

    stats = media_handler.statistics(search="test1")
    assert len(stats) == 1

    stats = media_handler.statistics(orderby="displayname", forward=True)
    assert stats[0]["user_id"] == "@admin1:localhost"
    assert len(stats) == 2

    with pytest.raises(ValueError):
        media_handler.statistics(orderby="invalid")


def test_media_list_media():
    assert post_media()
    returned = media_handler.list_media(reference_room).local
    assert sorted(returned) == sorted(media_id[:2])


def test_media_protect_media():
    protected_media = media_id[0]
    assert query_media(protected_media).status_code == 200
    assert media_handler.protect_media(protected_media)
    assert query_media(protected_media).status_code == 200
    assert media_handler.quarantine_id(protected_media)
    assert query_media(protected_media).status_code == 200

    with pytest.raises(SynapseException):
        media_handler.protect_media("invalid")


def test_media_unprotect_media():
    protected_media = media_id[0]
    assert media_handler.unprotect_media(protected_media)
    assert media_handler.quarantine_id(protected_media)
    assert query_media(protected_media).status_code == 404

    with pytest.raises(SynapseException):
        media_handler.unprotect_media("invalid")


def test_media_quarantine_id():
    quarantined_media = media_id[-2]
    assert media_handler.quarantine_id(quarantined_media)
    assert query_media(quarantined_media).status_code == 404


def test_media_quarantine_room():
    assert media_handler.quarantine_room(reference_room) == 2
    media1 = media_id[0]
    media2 = media_id[1]
    assert query_media(media1).status_code == 404
    assert query_media(media2).status_code == 404


def test_media_quarantine_user():
    assert media_handler.quarantine_user("admin1")
    quarantined_media = media_id[2:]
    for media in quarantined_media:
        assert query_media(media).status_code == 404


def test_media_quarantine_remove():
    quarantined_media = media_id[-1]
    assert query_media(quarantined_media).status_code == 404

    media_handler.quarantine_remove(quarantined_media)
    assert query_media(quarantined_media).status_code == 200


def test_media_delete_local_media():
    delete_media = media_id[0]
    assert media_handler.delete_local_media(delete_media)
    assert query_media(delete_media).status_code == 404

    with pytest.raises(SynapseException):
        media_handler.delete_local_media("invalid")


def test_media_purge_remote_media():
    assert media_handler.purge_remote_media() == 0


def test_media_delete_media():
    assert media_handler.delete_media(size_gt=1000000000) == []
    assert media_handler.delete_media(media_id[2])
    assert media_handler.delete_media(remote=True) == 0
    with pytest.raises(ValueError):
        media_handler.delete_media("invalid", keep_profiles=True)


def test_media_delete_local_media_by_condition():
    """TODO: timestamp, keep_profiles"""
    assert media_handler.delete_local_media_by_condition(size_gt=9665784) == []
    deleted_media = media_id[-1]
    assert query_media(deleted_media).status_code == 200

    delete_time = Utility.get_current_time() + 1000

    assert media_handler.delete_local_media_by_condition(
        delete_time,
        9000000
    ) == [media_handler.extract_media_id(deleted_media)]
    assert query_media(deleted_media).status_code == 404

    assert media_handler.delete_local_media_by_condition(
        delete_time,
        10000000
    ) == []

    deletion = media_handler.delete_local_media_by_condition(delete_time)
    assert deletion.total == 2
    for media in media_id:
        assert query_media(media).status_code == 404
