import os
import sys
import pyloren
from argparse import ArgumentParser, HelpFormatter
from io import TextIOBase


class BaseCommand:
    _called_from_command_line = True

    def create_parser(self, name, subcommand, **kwargs):
        parser = CommandParser(
            prog="{} {}".format(os.path.basename(name), subcommand),
            description=self.help or None,
            formatter_class=HelpFormatter,
            called_from_command_line=getattr(self, '_called_from_command_line', None),
            missing_args_message=getattr(self, 'missing_args_message', ''),
            **kwargs
        )
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        pass

    def print_help(self, name, subcommand):
        parser = self.create_parser(name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv):
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        cmd_options = vars(options)

        args = cmd_options.pop('args', ())

        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            sys.stderr.write('{}: {}'.format(e.__class__.__name__, e))
            sys.exit(1)

    def execute(self, *args, **options):
        output = self.handle(*args, **options)
        return output

    def handle(self, *arg, **options):
        raise NotImplementedError()


class CommandParser(ArgumentParser):
    def __init__(self, *, missing_args_message=None, called_from_command_line=None, **kwargs):
        self.missing_args_message = missing_args_message
        self.called_from_command_line = called_from_command_line
        super().__init__(**kwargs)

    def parse_args(self, args=None, namespace=None):
        if (self.missing_args_message and
                not (args or any(not arg.startswith('-') for arg in args))):
            self.error(self.missing_args_message)
        return super().parse_args(args, namespace)

    def error(self, message):
        if self.called_from_command_line:
            super().error(message)
        else:
            raise Exception("Error: %s" % message)
