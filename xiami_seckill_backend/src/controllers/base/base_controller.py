import threading

class BaseController(object):

    def execute_in_thread(self, func, args):
        t = threading.Thread(target=func, args=args)
        t.daemon = True
        t.start()