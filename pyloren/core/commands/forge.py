import os
import sys
import shutil
import stat
import pyloren
from pyloren.core.base import BaseCommand
from pyloren.utils import handle_extensions

TEMPLATE_FOLDER_NAME = "package_name"


class Command(BaseCommand):
    help = (
        "Creates a Python package directory structure for the given project "
        "name in the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide a package name."
    template_suffix_mapping = {'.py-tpl': '.py'}

    def add_arguments(self, parser):
        parser.add_argument('name', help='Name of the package.')
        parser.add_argument('directory', nargs='?', help='Optional destination directory')
        parser.add_argument(
            '--extension', '-e', dest='extensions',
            action='append', default=['py'],
            help='The file extension(s) to render (default: "py"). '
                 'Separate multiple extensions with commas, or use '
                 '-e multiple times.'
        )
        parser.add_argument(
            '--name', '-n', dest='files',
            action='append', default=[],
            help='The file name(s) to render. Separate multiple file names '
                 'with commas, or use -n multiple times.'
        )

    def handle(self, **options):
        name = options.pop('name')
        directory = options.pop('directory')
        self.validate_name(name)

        if directory is None:
            top_dir = os.path.join(os.getcwd(), name)
            try:
                os.makedirs(top_dir)
            except FileExistsError:
                raise Exception("'{}' already exists".format(top_dir))
            except OSError as e:
                raise Exception(e)
        else:
            top_dir = os.path.abspath(os.path.expanduser(directory))
            if not os.path.exists(top_dir):
                raise Exception("Directory {} does not exist yet, "
                                "please create it first.".format(top_dir))

        extensions = tuple(handle_extensions(options['extensions']))
        template_dir = os.path.join(pyloren.__path__[0], 'structure')
        prefix_length = len(template_dir) + 1

        for root, dirs, files in os.walk(template_dir):
            folder_name = root[prefix_length:].replace(TEMPLATE_FOLDER_NAME, name)
            if folder_name:
                new_dir = os.path.join(top_dir, folder_name)
                if not os.path.exists(new_dir):
                    os.mkdir(new_dir)

            """
            TODO: Handle this code to optimize performance
            for folder_name in dirs:
                template_dir = os.path.join(template_dir, folder_name)
                new_folder_name = name if folder_name == TEMPLATE_FOLDER_NAME else folder_name
                if suffix_path:
                    new_dir = os.path.join(top_dir, )
                new_dir = os.path.join(top_dir, new_folder_name)
                if not os.path.exists(new_dir):
                    os.mkdir(new_dir)

            """

            for filename in files:
                template_path = os.path.join(root, filename)
                package_path = os.path.join(top_dir, folder_name, filename)
                for tmp_suffix, new_suffix in self.template_suffix_mapping.items():
                    if package_path.endswith(tmp_suffix):
                        package_path = package_path[:-len(tmp_suffix)] + new_suffix
                        break
                if os.path.exists(package_path):
                        raise Exception("{} already exists.".format(package_path))

                if package_path.endswith(extensions):
                    with open(template_path, 'r', encoding='utf-8') as template_file:
                        content = template_file.read()
                    with open(package_path, 'w', encoding='utf-8') as new_file:
                        new_file.write(content)
                else:
                    shutil.copyfile(template_path, package_path)

                try:
                    shutil.copymode(template_path, package_path)
                    self.make_writeable(package_path)
                except OSError:
                    sys.stderr.write(
                        "Notice: Couldn't set permission bits on {}. You're "
                        "probably using an uncommon filesystem setup. No "
                        "problem.".format(new_path)
                    )

    def validate_name(self, name):
        if not name.isidentifier():
            raise Exception(
                "'{}' is not a valid package name. Please make sure the name "
                "is valid.".format(name)
            )

        existed_pip_packages = os.popen('pip search {}'.format(name)).read()
        if existed_pip_packages:
            raise Exception(
                "Package name '{}' is already existed on pipy. "
                "Please choose another one."
            )

    def make_writeable(self, filename):
        """
        Make sure that the file is writeable.
        Useful if our source is read-only.
        """
        if not os.access(filename, os.W_OK):
            st = os.stat(filename)
            new_permissions = stat.S_IMODE(st.st_mode) | stat.S_IWUSR
            os.chmod(filename, new_permissions)
