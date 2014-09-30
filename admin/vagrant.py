"""
Tools for interacting with vagrant.
"""

import sys
import os

import json

from flocker import __version__

from admin.runner import run


def box_metadata(name, version, path):
    """
    Generate metadata for a vagrant box.

    This metadate can be used to locally(!) add the box to vagrant,
    with the correct version, for testing.

    :param FilePath path: Directory containting ``Vagrantfile``.
    :param bytes name: Base name of vagrant box. Used to build filename.
    :param bytes version: Version of vagrant box. Used to build filename.
    """
    # Vagrant doesn't like - in version numbers.
    # It also doesn't like _ but we don't generate that.
    dotted_version = version.replace('-', '.')
    return {
        "name": "clusterhq/%s" % (name,),
        "description": "Test clusterhq/%s box." % (name,),
        "versions": [{
            "version": dotted_version,
            "providers": [{
                "name": "virtualbox",
                "url": path.path
                }]
            }]
        }


def build_box(path, name, version, branch):
    """
    Build a vagrant box.

    :param FilePath path: Directory containting ``Vagrantfile``.
    :param bytes name: Base name of vagrant box. Used to build filename.
    :param bytes version: Version of vagrant box. Used to build filename.
    :param bytes branch: Branch to get flocker RPMs from.
    """
    box_path = path.child('%s%s%s.box'
                          % (name, '-' if version else '', version))
    json_path = path.child('%s.json' % (name,))

    # Destroy the box to begin, so that we are guaranteed
    # a clean build.
    run(['vagrant', 'destroy', '-f'], cwd=path.path)

    env = os.environ.copy()
    env.update({
        'FLOCKER_VERSION': version.replace('-', '_'),
        'FLOCKER_BRANCH': branch,
        })
    run(['vagrant', 'up'], cwd=path.path, env=env)
    run(['vagrant', 'package', '--output', box_path.path], cwd=path.path)

    # And destroy at the end to save space.  If one of the above commands fail,
    # this will be skipped, so the image can still be debugged.
    run(['vagrant', 'destroy', '-f'], cwd=path.path)

    metadata = box_metadata(name, version, box_path)
    json_path.setContent(json.dumps(metadata))


def main(args, base_path, top_level):
    if base_path.basename() == 'build':
        path = base_path.parent()
        box = path.basename()
    else:
        try:
            box = args.pop(0)
        except IndexError:
            sys.stderr.write("build-vagrant-box: must specify box\n")
            raise SystemExit(1)
        path = top_level.descendant(['vagrant', box])

    if args:
        branch = args.pop(0)
    else:
        branch = ''

    version = __version__

    if args:
        sys.stderr.write("build-vagrant-box: too many arguments\n")
        raise SystemExit(1)

    sys.stdout.write("Building %s box from %s.\n" % (box, path.path))
    build_box(path, 'flocker-' + box, version, branch)
