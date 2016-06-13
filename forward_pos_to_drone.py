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

        print 'Position: (' + str(body.position.x) + ', ' + str(-body.position.y) + ', ' + str(-body.position.z) + ')'
	print 'Rotation: (' + str(body.rotation.z) + ', ' + str(-body.rotation.y) + ', ' + str(-body.rotation.x) + ')'
	print ''

	# Reconvert the euler angles back to quaternions
	# The natnet code stores the received quaternions as euler angles
	# Equations taken from en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
	# N.B. 	The outputted rotation angles are in degrees
	heading = -body.rotation.x # Natnet outputs yaw negated
	attitude = -body.rotation.y # Natnet outputs pitch negated
	bank = body.rotation.z
	
	deg2rad = math.pi / 180
	c1 = math.cos(deg2rad * heading / 2)
	c2 = math.cos(deg2rad * attitude / 2)
	c3 = math.cos(deg2rad * bank / 2)
	s1 = math.sin(deg2rad * heading / 2)
	s2 = math.sin(deg2rad * attitude / 2)
	s3 = math.sin(deg2rad * bank / 2)

	qw = c1 * c2 * c3 + s1 * s2 * s3
	qyaw = s1 * c2 * c3 - c1 * s2 * s3
	qpitch = c1 * s2 * c3 + s1 * c2 * s3
	qroll = c1 * c2 * s3 - s1 * s2 * c3

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
