######################################################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
######################################################################################################################

import boto3.session
import json
import random
from random import choice
import time
from datetime import datetime
import uuid
import os
import numpy
import argparse

# Event Payload defaults
DEFAULT_EVENT_VERSION = '1.0'
DEFAULT_BATCH_SIZE = 100

def parse_cmd_line():
    """Parse the command line and extract the necessary values."""

    parser = argparse.ArgumentParser(description='Send data to a Kinesis stream for analytics. By default, the script '
                                                 'will send events infinitely. If an input file is specified, the '
                                                 'script will instead read and transmit all of the events contained '
                                                 'in the file and then terminate.')

    # REQUIRED arguments
    kinesis_regions = boto3.session.Session().get_available_regions('kinesis')
    parser.add_argument('--region', required=True, choices=kinesis_regions, type=str,
                        dest='region_name', metavar='kinesis_aws_region',
                        help='The AWS region where the Kinesis stream is located.')
    parser.add_argument('--stream-name', required=True, type=str, dest='stream_name',
                        help='The name of the Kinesis stream to publish to. Must exist in the specified region.')
    parser.add_argument('--application-id', required=True, type=str, dest='application_id',
                        help='The application_id to use when submitting events to ths stream (i.e. You can use the default application for testing).')
    # OPTIONAL arguments
    parser.add_argument('--batch-size', type=int, dest='batch_size', default=DEFAULT_BATCH_SIZE,
                        help='The number of events to send at once using the Kinesis PutRecords API.')
    parser.add_argument('--input-filename', type=str, dest='input_filename',
                        help='Send events from a file rather than randomly generate them. The format of the file'
                             ' should be one JSON-formatted event per line.')

    return parser.parse_args()

# Returns array of UUIDS. Used for generating sets of random event data
def getUUIDs(dataType, count):
    uuids = []
    for i in range(0, count):
        uuids.append(str(uuid.uuid4()))
    return uuids    

# Randomly choose an event type from preconfigured options
def getEventType():
  event_types = {
        1: 'user_registration',
        2: 'user_kill',
        3: 'item_viewed',
        4: 'iap_transaction',
        5: 'login',
        6: 'logout',
        7: 'tutorial_progression',
        8: 'user_rank_up',
        9: 'matchmaking_start',
        10: 'matchmaking_complete',
        11: 'matchmaking_failed',
        12: 'match_start',
        13: 'match_end',
        14: 'level_started',
        15: 'level_completed',
        16: 'level_failed',
        17: 'lootbox_opened',
        18: 'user_report',
        19: 'user_sentiment'
  }
  return event_types[random.randint(1,19)]
  
# Generate a randomized event from preconfigured sample data
def getEvent(event_type):
    
    levels = [
        '1',
        '2',
        '3',
        '4',
        '5'
    ]
    
    countries = [
        
        'UNITED STATES',
        'UK',
        'JAPAN',
        'SINGAPORE',
        'AUSTRALIA',
        'BRAZIL',
        'SOUTH KOREA',
        'GERMANY',
        'CANADA',
        'FRANCE'
    ]

    items = getUUIDs('items', 10)
    
    currencies = [
        'USD',
        'EUR',
        'YEN',
        'RMB'
    ]
    
    platforms = [
        'nintendo_switch',
        'ps4',
        'xbox_360',
        'iOS',
        'android',
        'pc',
        'fb_messenger'
    ]

    tutorial_screens = [
        '1_INTRO',
        '2_MOVEMENT',
        '3_WEAPONS',
        '4_FINISH',
    ]

    match_types = [
        '1v1',
        'TEAM_DM_5v5',
        'CTF'
    ]

    matching_failed_msg = [
        'timeout',
        'user_quit',
        'too_few_users'
    ]

    maps = [
        'WAREHOUSE',
        'CASTLE',
        'AIRPORT'
    ]

    game_results = [
        'WIN',
        'LOSE',
        'KICKED',
        'DISCONNECTED',
        'QUIT'
    ]

    weapons = [
        'KNIFE',
        'SHOTGUN',
        'AR-15'
    ]
    
    ranks = [
        '1_BRONZE',
        '2_SILVER',
        '3_GOLD',
        '4_PLATINUM',
        '5_DIAMOND',
        '6_MASTER'
    ]
    
    item_rarities = [
        'COMMON',
        'UNCOMMON',
        'RARE',
        'LEGENDARY'
        
    ]
    
    report_reasons = [
        'GRIEFING',
        'CHEATING',
        'AFK',
        'RACISM/HARASSMENT'
        
    ]
    
    switcher = {
        'login': {
            'event_data': {
                'platform': str(numpy.random.choice(platforms, 1, p=[0.2, 0.1, 0.3, 0.15, 0.1, 0.05, 0.1])[0]),
                'last_login_time': int(time.time())-random.randint(40000,4000000)
            }
        },
        
        'logout': {
            'event_data': {
                'last_screen_seen': 'the last screen'
            }
        },
        
        'client_latency': {
            'event_data': {
                'latency': numpy.random.choice((random.randint(40,185),1)),
                'connected_server_id': str(random.choice(SERVERS)),
                'region': str(random.choice(countries))   
            }
        },
        
        'user_registration': {
            'event_data': {
                'country_id': str(numpy.random.choice(countries, 1, p=[0.3, 0.1, 0.2, 0.05, 0.05, 0.02, 0.15, 0.05, 0.03, 0.05])[0]),
                'platform': str(numpy.random.choice(platforms, 1, p=[0.2, 0.1, 0.3, 0.15, 0.1, 0.05, 0.1])[0])
            }
        },
        
        'user_kill': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'map_id': str(numpy.random.choice(maps, 1, p=[0.6, 0.3, 0.1])[0]),
                'clan_id': str(random.choice(CLANS)),
                'user_killed_id': str(random.choice(USERS)),
                'user_killed_clan_id': str(random.choice(CLANS)),
                'weapon_id': str(numpy.random.choice(weapons, 1, p=[0.1, 0.4, 0.5])[0]),
                'exp_gained': random.randint(1,2)
            }
        },
        
         'item_viewed': {
             'event_data': {
                'item_id': str(numpy.random.choice(items, 1, p=[0.125, 0.11, 0.35, 0.125, 0.04, 0.01, 0.07, 0.1, 0.05, 0.02])[0]),
                'item_version': random.randint(1,2)
            }
        },

        'iap_transaction': {
            'event_data': {
                'item_id': str(numpy.random.choice(items, 1, p=[0.125, 0.11, 0.35, 0.125, 0.04, 0.01, 0.07, 0.1, 0.05, 0.02])[0]),
                'item_version': random.randint(1,2),
                'item_amount': random.randint(1,4),
                'currency_type': str(numpy.random.choice(currencies, 1, p=[0.7, 0.15, 0.1, 0.05])[0]),
                'country_id': str(numpy.random.choice(countries, 1, p=[0.3, 0.1, 0.2, 0.05, 0.05, 0.02, 0.15, 0.05, 0.03, 0.05])[0]),
                'currency_amount': random.randint(1,10),
                'transaction_id': str(uuid.uuid4())
            }
        },
    
        'tutorial_progression': {
            'event_data': {
                'tutorial_screen_id': str(numpy.random.choice(tutorial_screens, 1, p=[0.3, 0.3, 0.2, 0.2])[0]),
                'tutorial_screen_version': random.randint(1,2)
            }
        },

        'user_rank_up': {
            'event_data': {
                'user_rank_reached': str(numpy.random.choice(ranks, 1, p=[0.25, 0.35, 0.2, 0.15, 0.0499, 0.0001])[0])
            }
        },
        
        'matchmaking_start': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'match_type': str(numpy.random.choice(match_types, 1, p=[0.4, 0.3, 0.3])[0])
            }
        },

        'matchmaking_complete': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'match_type': str(numpy.random.choice(match_types, 1, p=[0.6, 0.2, 0.2])[0]),
                'matched_slots': random.randrange(start=6, stop=10)
            }
        },

        'matchmaking_failed': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'match_type': str(numpy.random.choice(match_types, 1, p=[0.35, 0.2, 0.45])[0]),
                'matched_slots': random.randrange(start=1, stop=10),
                'matching_failed_msg': str(numpy.random.choice(matching_failed_msg, 1, p=[0.35, 0.2, 0.45])[0])
            }
        },

        'match_start': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'map_id': str(numpy.random.choice(maps, 1, p=[0.3, 0.3, 0.4])[0]),
                'clan_id': str(random.choice(CLANS)),
            }
        },

        'match_end': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'map_id': str(numpy.random.choice(maps, 1, p=[0.3, 0.3, 0.4])[0]),
                'clan_id': str(random.choice(CLANS)),
                'match_result_type': str(numpy.random.choice(game_results, 1, p=[0.4, 0.4, 0.05, 0.05, 0.1])[0]),
                'exp_gained': random.randrange(start=100, stop=200),
                'most_used_weapon': str(numpy.random.choice(weapons, 1, p=[0.1, 0.4, 0.5])[0])
            }
        },
        
        'level_started': {
            'event_data': {
                'level_id': str(numpy.random.choice(levels, 1, p=[0.2, 0.2, 0.2, 0.2, 0.2])[0]),
                'level_version': random.randint(1,2)
            }
        },
        'level_completed': {
            'event_data': {
                'level_id': str(numpy.random.choice(levels, 1, p=[0.4, 0.25, 0.2, 0.1, 0.05])[0]),
                'level_version': random.randint(1,2)
            }
        },
        'level_failed': {
            'event_data': {
                'level_id': str(numpy.random.choice(levels, 1, p=[0.001, 0.049, 0.05, 0.3, 0.6])[0]),
                'level_version': random.randint(1,2)
            }
        },
        
        'lootbox_opened': {
            'event_data': {
                'lootbox_id': str(uuid.uuid4()),
                'lootbox_cost': random.randint(2,5),
                'item_rarity': str(numpy.random.choice(item_rarities, 1, p=[0.5, 0.3, 0.17, .03])[0]),
                'item_id': str(numpy.random.choice(items, 1, p=[0.125, 0.11, 0.35, 0.125, 0.04, 0.01, 0.07, 0.1, 0.05, 0.02])[0]),
                'item_version': random.randint(1,2),
                'item_cost': random.randint(1,5)
            }
        },
        
        'user_report': {
            'event_data': {
                'report_id': str(uuid.uuid4()),
                'reported_user': str(random.choice(USERS)),
                'report_reason': str(numpy.random.choice(report_reasons, 1, p=[0.2, 0.5, 0.1, 0.2])[0])
            }
        },
        
        'user_sentiment': {
            'event_data': {
                'user_rating': random.randint(1,5)
            }
        }
    }
    
    return switcher[event_type]
    

# Take an event type, get event data for it and then merge that event-specific data with the default event fields to create a complete event
def generate_event():
    event_type = getEventType()
    
    # Within the demo script the event_name is set same as event_type for simplicity.
    # In many use cases multiple events could exist under a common event type which can enable you to build a richer data taxonomy.
    event_name = event_type
    event_data = getEvent(event_type)
    event = {
        'event_version': DEFAULT_EVENT_VERSION,
        'event_id': str(uuid.uuid4()),
        'event_type': event_type,
        'event_name': event_name,
        'event_timestamp': int(time.time()),
        'client_id': str(random.choice(CLIENTS)),
        'user_id': str(random.choice(USERS)),
        'session_id': str(random.choice(SESSIONS))
    }
    
    event.update(event_data)
    return event
    
def send_record_batch(kinesis_client, stream_name, raw_records):
    """Send a batch of records to Amazon Kinesis."""

    # Translate input records into the format needed by the boto3 SDK
    formatted_records = []
    for rec in raw_records:
        formatted_records.append({'PartitionKey': rec['event']['client_id'], 'Data': json.dumps(rec)})
    kinesis_client.put_records(StreamName=stream_name, Records=formatted_records)
    print('Sent %d records to stream %s.' % (len(formatted_records), stream_name))

def send_events_infinite(kinesis_client, stream_name, batch_size, registration_id):
    """Send a batches of randomly generated events to Amazon Kinesis."""
    
    while True:
        records = []

        # Create a batch of random events to send
        for i in range(0, batch_size):
            event_dict = generate_event()
            record = {
                'event': event_dict,
                'application_id': application_id
            }
            records.append(record)
        send_record_batch(kinesis_client, stream_name, records)
        time.sleep(1.0)

if __name__ == '__main__':
    args = parse_cmd_line()
    aws_region = args.region_name
    kinesis_stream = args.stream_name
    batch_size = args.batch_size or DEFAULT_BATCH_SIZE
    application_id = args.application_id
    
    print('===========================================')
    print('CONFIGURATION PARAMETERS:')
    print('- KINESIS_STREAM: ' + kinesis_stream)
    print('- AWS_REGION: ' + aws_region)
    print('- APPLICATION_ID: ' + application_id)
    CLIENTS = getUUIDs('clients', 115)
    USERS = getUUIDs('users', 115)
    SERVERS = getUUIDs('servers', 3)
    CLANS = getUUIDs('clans', 5)
    MATCHES = getUUIDs('matches', 50)
    SESSIONS = getUUIDs('sessions', 115)
    print('Generated ' + str(len(CLIENTS)) + ' clients')
    print('Generated ' + str(len(USERS)) + ' users')
    print('Generated ' + str(len(SERVERS)) + ' servers')
    print('Generated ' + str(len(CLANS)) + ' clans')
    print('Generated ' + str(len(MATCHES)) + ' matches')
    print('Generated ' + str(len(SESSIONS)) + ' sessions')
    print('===========================================\n')
    
    session = boto3.Session(profile_name='default')
    client = session.client('kinesis', region_name=aws_region)
    
    send_events_infinite(client, kinesis_stream, batch_size, application_id)