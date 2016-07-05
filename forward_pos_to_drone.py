import natnetclient as natnet
import dronekit
import argparse
import time
import sys
import math

if __name__ == "__main__":

    # Command line arguments
    parser = argparse.ArgumentParser(description='Simple program that forwards object position to drone.')
    parser.add_argument('--natnet_ip', dest='natnet_ip', action='store', type=str, default='192.168.0.100',
                       help='IP of the machine running Optitrack Motive (default: 192.168.0.100)')
    parser.add_argument('--mav_link', dest='mav_link', action='store', type=str, default='udp:127.0.0.1:14551',
                       help='Interface to the drone (default: udp:127.0.0.1:14551)')
    parser.add_argument('--body_name', dest='body_name', action='store', type=str, default="Star_destroyer",
                       help='The body name of the optitrack rigid body, if not inputted, will send first key')
    parser.add_argument('-v', "--verbose", action='store_true', help='Turns on verbose messages.')
    args = parser.parse_args()

    # Connect to Motive
    try:
        client = natnet.NatClient(client_ip=args.natnet_ip,
                                  data_port=1511,
                                  comm_port=1510)
    except Exception as e:
        print("Could not connect to NatNet computer at IP " + args.natnet_ip)
        print(e)
        sys.exit(0)

    # Connect to the drone
    vehicle = dronekit.connect(args.mav_link, wait_ready=False, rate=200, heartbeat_timeout=0)

    while True:
        # Do this at ~10Hz
        time.sleep(0.1)

        # Get first body
        if args.body_name == None:
            body_name = client.rigid_bodies.keys()[0]
        else:
            body_name = args.body_name
        body = client.rigid_bodies[body_name]

        if body.seen == True:
            qw = body.rotation[3]
            qroll = body.rotation[0]
            qpitch = -body.rotation[1]
            qyaw = -body.rotation[2]
			
			if args.verbose:
				print 'Position: (' + str(body.position.x) + ', ' + str(-body.position.y) + ', ' + str(-body.position.z) + ')'
			print 'Rotation: (' + str(qw) + ', ' + str(qroll) + ', ' + str(qpitch) + ', ' + str(qyaw) + ')'
			print ''

			# Prepare message for drone
			msg = vehicle.message_factory.att_pos_mocap_encode(time_usec=time.time(),
															   q=[qw, qroll, qpitch, qyaw],
															   x=body.position.x,
															   y=-body.position.y,
															   z=-body.position.z)

			# Send message
			vehicle.send_mavlink(msg)

		# notify connexion LOSS
		if vehicle.last_heartbeat > 5:
			print("Connexion lost")
