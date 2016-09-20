# -*- coding: utf-8 -*-
'''
This script tests if one or multiple templates can be rendered using Jinja2.
It also can check the expected output difference.
It populates the variables in for the jinja templates using yaml files.

Arguments:

  -r, --root-dir:
       Root directory to scan for *.tmpl files. Ignored with -t option.
       Defaults to the parent directory of this script location.

  -d, --default-yaml-file:
      Default yaml file to fetch the variables in.
      Defaults to the file jinja_validator.yaml in the script directory.

      WARNING: If a file exist in the same path as the template file, using the
      same name as the template, but with a suffix '.jval.yaml', this yaml file
      will be the only one taken in account.

  -t, --template:
      Path to the template to test (takes all the *.tmpl files if empty)

  -f, --template-final:
      If specified with the --template option, will check that the render of the
      template will look like the value of the file specified.
      If not specified, the script will look for files existing in the same
      directory as the template but with a '.rendered' suffix and compared the
      output of the rendered template to it.
      If not specified and no '.rendered' file exist, only the fact that the
      render completes will be checked (aka. only a syntax check is done)

Changelog:

2016-02-10 Release 0.1.1:
 - Adding the support of dynamic expected render result files
 - Adding some documentation
2016-02-09 Release 0.1.0:
 - Initial version
'''
import os
import sys
import argparse
import logging
import yaml
from jinja2 import Environment

# The default root environment is one step before the directory of this script
ROOT_ENV = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
# The default yaml that contains the variables of the tests
DEFAULT_YAML = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'jinja_validator.yaml')
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level='INFO')

def validate_template(tmpl, tmpl_vars, expected_result):
    '''
    This function tries to render the template you give as parameter.

    Parameters:
      - tmpl: the name of the template to try to render
      - tmpl_vars: the variables to use with the template
      - end_result: A string containing exactly what the end result should look
        like
    '''
    with open(tmpl, 'r') as handle:
        template_source = handle.read()
        env = Environment()
        template = env.from_string(template_source)
        try:
            rend = template.render(tmpl_vars)

            if len(expected_result) > 0 and rend != expected_result:
                tempfile = '/tmp/last_rendering_err.log'
                with open(tempfile, 'w') as tmpfile:
                    tmpfile.write(rend)
                    logging.info("The rendered file has been dumped to %s", tempfile)
                logging.error("Unable to render file %s as expected", tmpl)
                return False
            else:
                logging.info("Template %s rendered successfully", tmpl)
                return True
        except Exception as ex:
            logging.error("Template tmpl failed with the error: %s", ex.message)
            return False

def process_file(root_folder, template_file, rendered_file):
    '''
    Takes a template file and process it (grabs the corresponding variables from
    the yaml, and call the validate_template function).

    Parameters:
      - root_folder: the root directory of the template file
      - template_file: the filename of the template
    '''
    # Loading the variables from the yaml file of the template of
    # exists. If not, load from the default one.
    yaml_file = args.default_yaml
    if os.path.isfile(os.path.join(root_folder, template_file + '.jval.yaml')):
        yaml_file = os.path.join(root_folder, template_file + '.jval.yaml')

    expected_render = ''
    default_render_path = os.path.join(root_folder, template_file + '.rendered')
    # If a render file is specifile, take it.
    if len(rendered_file) > 0:
        with open(rendered_file, 'r') as handle:
            expected_render = handle.read()
    # If not, try the default render file pattern
    elif os.path.isfile(default_render_path):
        with open(default_render_path, 'r') as handle:
            expected_render = handle.read()
    else:
        logging.debug("No render file available. Will not compare the result.")

    with open(yaml_file, 'r') as yfile:
        template_variables = yaml.load(yfile)
        logging.debug("Loaded from yaml: %r", template_variables)
        return validate_template(os.path.join(root_folder, template_file),
                                 template_variables, expected_render)

if __name__ == "__main__":

    opts = argparse.ArgumentParser(description='Validates jinja2 templates.')

    opts.add_argument('-r', '--root-dir', dest="root_dir", metavar="ROOTDIR",
                      default=ROOT_ENV,
                      help="Root directory to scan for *.tmpl files. Ignored with -t option.")
    opts.add_argument('-d', '--default-yaml-file', dest='default_yaml',
                      metavar='ROOT_YAML', default=DEFAULT_YAML,
                      help="Default yaml file to fetch the variables in.")
    opts.add_argument('-t', '--template', dest='template', metavar='TEMPLATE',
                      help="Template to test (takes all the *.tmpl files if empty)")
    opts.add_argument('-f', '--template-final', dest='template_final',
                      metavar='TEMPLATE_FINAL', default='',
                      help="If specified with the --template option, will check that the render of the template will look like the value of the file specified.")

    args = opts.parse_args()
    returned_status = True
    if args.template:
        if os.path.isfile(args.template):
            returned_status = process_file(
                os.path.dirname(args.template),
                os.path.basename(args.template),
                args.template_final)
            if not returned_status:
                sys.exit(1)
        else:
            logging.error("Invalid template path: %s", args.template)
            sys.exit(1)
    else:
        for root, dirs, files in os.walk(args.root_dir):
            for f in files:
                if f.endswith(".tmpl"):
                    returned_status = process_file(root, f, args.template_final)
                    if not returned_status:
                        sys.exit(1)
