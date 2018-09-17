DEFAULT_SH_SCRIPT = '''#!/bin/bash
        source /home/ubuntu/anaconda3/bin/activate %s_p36
        pip install -r requirements.txt --quiet --upgrade
        pip install mantraml --quiet
        mantra train %s --dataset %s --cloudremote %s'''

DEFAULT_SH_SCRIPT_VERBOSE = '''#!/bin/bash
        source /home/ubuntu/anaconda3/bin/activate %s_p36
        pip install -r requirements.txt --upgrade
        pip install mantraml
        mantra train %s --dataset %s --cloudremote %s'''

DEFAULT_SH_TASK_SCRIPT = '''#!/bin/bash
        source /home/ubuntu/anaconda3/bin/activate %s_p36
        pip install -r requirements.txt --quiet --upgrade
        pip install mantraml --quiet
        mantra train %s --dataset %s --task %s --cloudremote %s'''

DEFAULT_SH_TASK_SCRIPT_VERBOSE = '''#!/bin/bash
        source /home/ubuntu/anaconda3/bin/activate %s_p36
        pip install -r requirements.txt --upgrade
        pip install mantraml
        mantra train %s --dataset %s --task %s --cloudremote %s'''

MANTRA_DEVELOPMENT_TAG_NAME = 'mantra dev'

EXCLUDED_PROJECT_FILES = ["'raw/*'", "'results/*'", "'trials/*'", "'.extract*'", "'.mantra*'"]