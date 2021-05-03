import yaml

class Server:

    def __init__(self, sdict):

        self.instance_type = sdict['instance_type']
        self.ami_type = sdict['ami_type']
        self.architecture = sdict['architecture']
        self.root_device_type = sdict['root_device_type']
        self.virtualization_type = sdict['virtualization_type']
        self.min_count = sdict['min_count']
        self.max_count = sdict['max_count']
        self.volumes = sdict['volumes']
        self.users = sdict['users']

class Parameters:

    def __init__(self, file):

        with open(file, 'r') as f:
            params = yaml.safe_load(f)

        sdict = params['server']
        self.server = Server(sdict)
