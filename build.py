import datetime
import os
import subprocess
import sys
import textwrap
import tomllib


def get_version():
    with open(os.path.join(os.path.dirname(__file__), 'pyproject.toml'), 'rb') as f:
        pyproject = tomllib.load(f)
        return pyproject['project']['version']


def get_detailed_version():
    try:
        return (
            subprocess.run(
                ['git', 'describe', '--dirty', '--tags'], check=True, capture_output=True
            )
            .stdout.decode('utf-8')
            .strip()
        )
    except subprocess.CalledProcessError:
        return ''


def build():
    if sys.platform == 'win32':
        filename = 'libusb-1.0.dll'
        directory = os.path.abspath(os.path.dirname(__file__))
        if not os.path.exists(os.path.join(directory, filename)):
            print(
                textwrap.dedent(f"""\
                {filename} not found. Download it from
                https://github.com/libusb/libusb/releases and place in
                {directory}"""),
                file=sys.stderr,
            )
            sys.exit(1)

    with open('.version.txt', 'w') as f:
        f.write(get_version())
    with open('.version_info.txt', 'w') as f:
        f.write(get_detailed_version())
    with open('.build_date.txt', 'w') as f:
        f.write(datetime.date.today().isoformat())

    subprocess.run(['pyside6-rcc', 'resources.qrc', '-o', 'rc_resources.py'], check=True)

    os.remove('.version.txt')
    os.remove('.version_info.txt')
    os.remove('.build_date.txt')


def package():
    build()

    version = get_version()
    cmdline = [
        'nuitka' if sys.platform != 'win32' else 'nuitka.cmd',
        '--mode=onefile',
        '--enable-plugins=pyside6',
        '--include-qt-plugins=qml',
        '--file-description=Decent Configuration Console',
        '--product-name=Decent Configuration Console',
        f'--file-version={version}',
        f'--product-version={version}',
        '--main=main.py',
        '--output-dir=build',
        '--output-filename=decent-configuration-console',
    ]
    if sys.platform == 'win32':
        cmdline.append('--include-data-files=libusb-1.0.dll=libusb-1.0.dll')
        cmdline.append('--windows-console-mode=disable')
    else:
        cmdline.append('--linux-icon=decent.svg')
    subprocess.run(cmdline, check=True)


if __name__ == '__main__':
    action = (sys.argv[1:] + ['build'])[0]
    if len(sys.argv) > 2 or action not in ['build', 'package']:
        print('Usage: build.py {build|package}', file=sys.stderr)
        sys.exit(1)
    elif action == 'build':
        build()
    elif action == 'package':
        package()
