#import docker # would've been nice but no docker-compose like functionality
import wabbit_wappa
import socket

# Provide access to VWAPI
class VWAPI(object):
    """
    Simple class for defining a set of
    instatiation parameters for vowpal wabbit, access to

    Example Use:
    vw = VWAPI()
    res = vw.get_bulk_responses([[1,2,3], [3,4,5^]])
    print str(res[0]) + " is the first response"
    if res[0].importance > 0:
        print "This response has some importances attached to it"

    vw.vw.close() # del seems to take a while
    del vw

    # ... do somethign with the res variable ...
    """
    def __init__(self, task='relevance', host='VW_RELEVANCE'):
        # both vowpal wabbit relevance and product are initated by the NextML start up process
        # just need to bind a socket here.
        self.DEFAULT_PORT = 7000
        self.host = host

        HOST = self.host if host == 'VW_RELEVANCE' else host
        PORT = self.DEFAULT_PORT if task == 'relevance' else 9000 # for product
        # get socket to vowpal wabbit process (stood up by NextML)

        # note: Should I enable socket.SO_REUSEADDR? I don't think it's needed, esp if
        # the instance is deleted after use (closed socket). Very important to delete it though

        print('\t attempting to conenct to: ', HOST, PORT)

        # note: The vw.vw_process.sock is never really meant to be shutdown during normal use
        self.vw = wabbit_wappa.VW(daemon_ip=HOST,
                                  active_mode=True,
                                  daemon_mode=True,
                                  port=PORT)

        # can't do this after the fact ...
        #self.vw.vw_process.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __del__(self): # in case we del an instance and or pass out of scope
        self.vw.close()

    # utility function to receive same number of responses as examples sent
    def recvall(self, sock, num_examples, buffer_size=4096):
        chunk = True
        ret = []
        while num_examples > 0 and chunk:
            chunk = sock.recv(buffer_size)# todo: should we have a timeout socket? This will block.
            chunk_list = chunk.decode('utf-8')[:-1].split('\n')
            ret.extend(chunk_list)
            #num_examples = num_examples - 1

            # so vw can actually return one or multiple examples per tcp response
            # ... we need to identify how many example were returned and decrement
            # appropriately. We trim the trailing new line to more easily count.
            #num_examples = num_examples - len(chunk[:-1].split('\n'))
            # decode('utf-8') in case if ran from python 3 instead of python 2
            #num_examples = num_examples - len(chunk.decode('utf-8')[:-1].split('\n'))
            num_examples = num_examples - len(chunk_list)

        # VW returns a new line on last line but we .split() raw responses
        # so we leave off the last new line so that we may easily parse the response
        #return "".join(ret)[:-1]
        return "\n".join(ret)

    def to_vw_examples(self,
                       examples,
                       example_format='string vector',
                       business_name=None,
                       region=None):
        vw_examples  = []
        num_examples = len(examples)

        print('\t\t type:', type(examples), ' type[0]', type(examples[0]))
        #print(examples[0:3])

        if 'numerical vector' == example_format:
            assert isinstance(examples[0], type([])), "get_bulk_responses: Examples are not in expect numerical array format!"

            for example in examples:
                vw_examples.append(wabbit_wappa.Namespace('default',
                            features = [('col'+str(idx), value)
                                            for idx, value in enumerate(example)]))

        elif 'self interacting string vector' == example_format:
            pass # stub for treating websites as a long sequence of strings

        elif 'string vector' == example_format: # can be unicode too
            print(examples[0][0], type(examples[0][0]))
            #print('\n', examples[0][0][0])

            # we want to check the elements as being strings below but ...
            #assert isinstance(examples[0][0], basestring), "get_bulk_responses: Examples are not array of strings!"

            # ... the above doesn't work in both Py 2 and Py 3
            # this fix works in both
            sample = examples[0][0]
            is_str = isinstance(sample, str) # works in Py 3, not Py 2
            if not is_str:
                try:
                    is_unicode = isinstance(sample, unicode)
                except NameError: # we're in Python 3 and its not unicode (str=unicode in py 3)
                    is_unicode = False

            assert is_str or is_unicode, "get_bulk_responses: Examples are not array of strings!"

            for example in examples:
                # added, verify works as expected
                vw_examples.append(wabbit_wappa.Namespace('default', features = example))

        else:
            raise NotImplementedError("to_vw_examples: example_format is not supported!")

        return vw_examples

    def get_bulk_responses(self, examples, business_name=None, region=None):
        # see: https://github.com/JohnLangford/vowpal_wabbit/wiki/Daemon-example
        # basically, send a newline to delimit each example, vw will respond back similarly

        # First convert raw examples into a vw friendly format...
        # note: this is task and data format specific: here we assume an array of floats
        num_examples = len(examples)
        vw_examples = self.to_vw_examples(examples, business_name=business_name, region=region)

        # we append a newline at end re: Daemon example
        to_send_examples = '\n'.join([self.vw.make_line(namespaces=[f])[:-1]
                                        for f in vw_examples]) + '\n'


        # get responses ...
        self.vw.vw_process.sock.sendall(to_send_examples.encode('utf-8'))
        raw_responses = self.recvall(self.vw.vw_process.sock, num_examples=num_examples)
        responses = [wabbit_wappa.VWResult(r, active_mode=True) for r in raw_responses.split('\n')]

        assert len(responses) == num_examples,\
            "get_bulk_responses, number recv'ed does not match number examples sent! sent {}, recved {}".format(num_examples, len(responses))
        # can access .prediction or .importance attribute
        return responses
