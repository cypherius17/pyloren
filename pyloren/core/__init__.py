import os
import sys
import pkgutil
import functools
from collections import defaultdict
from difflib import get_close_matches
from importlib import import_module
from pyloren.core.base import BaseCommand, CommandParser


def find_commands(core_dir):
    command_dir = os.path.join(core_dir, 'commands')
    return [name for _, name, is_pkg in pkgutil.iter_modules([command_dir])
            if not is_pkg and not name.startswith('_')]


@functools.lru_cache(maxsize=None)
def get_commands():
    commands = {name: 'pyloren.core' for name in find_commands(__path__[0])}
    return commands


def load_command_class(app_name, name):
    module = import_module('{}.commands.{}'.format(app_name, name))
    return module.Command()


class CommandHandler:
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.caller = os.path.basename(self.argv[0])
        if self.caller == "__main__.py":
            self.caller = "python -m pyloren"

    def main_help_text(self, commands_only=False):
        if commands_only:
            usage = sorted(get_commands())
        else:
            usage = [
                "",
                "Type '{} help <subcommand>' for help on a specific subcommand.".format(self.caller),
                "",
                "Available subcommands:",
            ]
            commands_dict = defaultdict(lambda: [])
            for name, app in get_commands().items():
                commands_dict[app].append(name)
            for app in sorted(commands_dict):
                usage.append("")
                for name in sorted(commands_dict[app]):
                    usage.append("{}".format(name))
        return '\n'.join(usage)

    def fetch_command(self, subcommand):
        commands = get_commands()
        try:
            app_name = commands[subcommand]
        except KeyError:
            possible_matches = get_close_matches(subcommand, commands)
            sys.stderr.write('Unknown command: {}'.format(subcommand))
            if possible_matches:
                sys.stderr.write('. Did you mean {}?'.format(possible_matches[0]))
            sys.stderr.write("\nType '{} help' for usage.\n".format(self.caller))
            sys.exit(1)
        if isinstance(app_name, BaseCommand):
            klass = app_name
        else:
            klass = load_command_class(app_name, subcommand)
        return klass

    def execute(self):
        """
        Given the command-line arguments, figure out which subcommand is run,
        create a parser appropriate to that command and run it.
        """
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = "help"

        try:
            parser = CommandParser()
            parser.add_argument('args', nargs='*')
            options, args = parser.parse_known_args(self.argv[2:])
        except Exception:
            pass

        # self.autocomplete()

        if subcommand == 'help':
            if '--commands' in args:
                sys.stdout.write(self.main_help_text(commands_only=True) + '\n')
            elif not options.args:
                sys.stdout.write(self.main_help_text() + '\n')
            else:
                self.fetch_command(options.args[0]).print_help(self.caller, options.args[0])
        elif self.argv[1:] in (['--help'], ['-h']):
            sys.stdout.write(self.main_help_text() + '\n')
        else:
            self.fetch_command(subcommand).run_from_argv(self.argv)

    def autocomplete(self):
        cwords = os.environ['COMP_WORDS'].split()[1:]
        cword = int(os.environ['COMP_CWORD'])

        try:
            curr = cwords[cword - 1]
        except IndexError:
            curr = ''

        subcommands = [*get_commands(), 'help']
        options = [('--help', False)]

        if cword == 1:
            print(' '.join(sorted(filter(lambda x: x.startswith(curr), subcommands))))
        elif cwords[0] in subcommands and cwords[0] != 'help':
            subcommand_cls = self.fetch_command(cwords[0])

            if cwords[0] in ('dumpdata', 'sqlmigrate', 'sqlsequencereset', 'test'):
                try:
                    app_configs = apps.get_app_configs()
                    options.extend((app_config.label, 0) for app_config in app_configs)
