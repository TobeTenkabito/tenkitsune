class Event(object):
    def __init__(self, name, description, start_time, end_time):
        self.name = name
        self.description = description
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return 'Event name: {}, description: {}'.format(self.name, self.description)
