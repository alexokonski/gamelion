from amqplib import client_0_8 as amqp

amqp_connection = amqp.Connection(
       host='localhost:5672',
       userid='gamelion',
       password='gamelion',
       virtual_host='/',
       insist=False
)
amqp_channel = amqp_connection.channel()

result = amqp_channel.queue_purge('servers')
print result, 'messages purged'

