import gutenbach.server
import sys
import os
import yaml

if len(sys.argv) != 2:
    print "Invalid number of arguments: %d" % len(sys.argv)
    sys.exit(1)

config = sys.argv[1]
if not os.path.exists(config):
    print "Invalid config: %s" % config
    sys.exit(1)

conf_dict = yaml.load(open(config, "r"))
print "Loaded configuration file:"
print conf_dict
    
gutenbach.server.start(conf_dict)
