# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import fileinput
import logging
import os
import shutil
import sys
from tempfile import mkdtemp
from urlparse import urlsplit, urlunsplit

import git
from celery import shared_task

from .models import Formula
from stackdio.api.formulas.validators import validate_specfile, validate_component

logger = logging.getLogger(__name__)


class FormulaTaskException(Exception):
    def __init__(self, formula, error):
        formula.set_status(Formula.ERROR, error)
        super(FormulaTaskException, self).__init__(error)


def replace_all(rep_file, search_exp, replace_exp):
    for line in fileinput.input(rep_file, inplace=True):
        if search_exp in line:
            line = line.replace(search_exp, replace_exp)
        sys.stdout.write(line)


def clone_to_temp(formula, git_password):
    # temporary directory to clone into so we can read the
    # SPECFILE and do some initial validation
    tmpdir = mkdtemp(prefix='stackdio-')
    reponame = formula.get_repo_name()
    repodir = os.path.join(tmpdir, reponame)

    uri = formula.uri
    # Add the password for a private repo
    if formula.private_git_repo:
        parsed = urlsplit(uri)
        hostname = parsed.netloc.split('@')[1]
        uri = urlunsplit((
            parsed.scheme,
            '{0}:{1}@{2}'.format(
                formula.git_username, git_password, hostname),
            parsed.path,
            parsed.query,
            parsed.fragment
        ))

    try:
        # Clone the repo into a temp dir
        repo = git.Repo.clone_from(uri, repodir)

        origin = repo.remotes.origin.name

        # Remove the password from the config
        repo.git.remote('set-url', origin, formula.uri)

        # Remove the logs which also store the password
        log_dir = os.path.join(repodir, '.git', 'logs')
        # if os.path.isdir(log_dir):
        shutil.rmtree(log_dir)

    except git.GitCommandError:
        raise FormulaTaskException(
            formula,
            'Unable to clone provided URI. This is either not '
            'a git repository, or you don\'t have permission to clone it.  '
            'Note that private repositories require the https protocol.')

    # return the path where the repo is
    return repodir


@shared_task(name='formulas.import_formula')
def import_formula(formula_id, git_password):
    formula = None
    try:
        formula = Formula.objects.get(id=formula_id)
        formula.set_status(Formula.IMPORTING, 'Cloning and importing formula.')

        repodir = clone_to_temp(formula, git_password)

        root_dir = formula.get_repo_dir()

        if os.path.isdir(root_dir):
            raise FormulaTaskException(
                formula,
                'Formula root path already exists.')

        formula_title, formula_description, root_path, components = validate_specfile(formula,
                                                                                      repodir)

        # update the formula title and description
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        # validate components
        for component in components:
            validate_component(formula, repodir, component)

        root_dir = formula.get_repo_dir()

        # move the cloned formula repository to a location known by salt
        # so we can start using the states in this formula
        shutil.move(repodir, root_dir)

        tmpdir = os.path.dirname(repodir)

        # remove tmpdir now that we're finished
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True
    except FormulaTaskException:
        raise
    except Exception as e:
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')


# TODO: Ignoring complexity issues
@shared_task(name='formulas.update_formula')
def update_formula(formula_id, git_password):
    repo = None
    current_commit = None
    formula = None

    try:
        formula = Formula.objects.get(pk=formula_id)
        formula.set_status(Formula.IMPORTING, 'Updating formula.')

        # Grab the components now before we pull
        old_components = formula.components

        repodir = formula.get_repo_dir()
        repo = formula.repo

        current_commit = repo.head.commit

        origin = repo.remotes.origin.name

        # Add the password for a private repo
        if formula.private_git_repo:
            parsed = urlsplit(formula.uri)
            hostname = parsed.netloc.split('@')[1]
            uri = urlunsplit((
                parsed.scheme,
                '{0}:{1}@{2}'.format(formula.git_username, git_password, hostname),
                parsed.path,
                parsed.query,
                parsed.fragment
            ))

            # add the password to the config
            repo.git.remote('set-url', origin, uri)

        result = repo.remotes.origin.pull()
        if len(result) == 1 and result[0].commit == current_commit:
            formula.set_status(Formula.COMPLETE,
                               'There were no changes to the repository.')
            return True

        if formula.private_git_repo:
            # remove the password from the config
            repo.git.remote('set-url', origin, formula.uri)

            # Remove the logs which also store the password
            log_dir = os.path.join(repodir, '.git', 'logs')
            if os.path.isdir(log_dir):
                shutil.rmtree(log_dir)

        formula_title, formula_description, root_path, components = validate_specfile(formula,
                                                                                      repodir)

        # Check for added or changed components
        added_components = []
        changed_components = []

        for component in components:
            # Check to see if the component was already in the formula
            exists = False
            for old_component in old_components:
                if component['sls_path'] == old_component['sls_path']:
                    # If we find a matching sls path,
                    # update the associated title and description
                    changed_components.append(component)
                    exists = True
                    break

            # if not, set it to be added
            if not exists:
                added_components.append(component)

        # validate new components
        for component in added_components:
            validate_component(formula, repodir, component)

        # validate changed components
        for component in changed_components:
            validate_component(formula, repodir, component)

        # Everything was validated, update the database
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True

    except Exception, e:
        # Roll back the pull
        if repo is not None and current_commit is not None:
            repo.git.reset('--hard', current_commit)
        if isinstance(e, FormulaTaskException):
            raise FormulaTaskException(
                formula,
                e.message + ' Your formula was not changed.')
        logger.exception(e)
        raise FormulaTaskException(
            formula,
            'An unhandled exception occurred.  Your formula was not changed')
