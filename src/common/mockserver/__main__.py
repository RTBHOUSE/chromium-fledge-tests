from . import MockServer

from argparse import ArgumentParser


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--port', '-p', type=int, required=True)
    argument_parser.add_argument('--directory', '-d', required=True)
    arguments = argument_parser.parse_args()
    server = MockServer(**vars(arguments))
    server.run()
