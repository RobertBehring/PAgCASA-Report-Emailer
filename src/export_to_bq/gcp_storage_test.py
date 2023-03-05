
import unittest

import main


def test_print(capsys):
    name = 'test'
    event = {
        'bucket': 'some-bucket',
        'name': name,
        'metageneration': 'some-metageneration',
        'timeCreated': '0',
        'updated': '0'
    }

    context = unittest.mock.MagicMock()
    context.event_id = 'some-id'
    context.event_type = 'gcs-event'

    # Call tested function
    main.get_new_data(event, context)
    out, err = capsys.readouterr()
    assert 'File: {}\n'.format(name) in out