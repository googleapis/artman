"""Tasks related to format"""

import os
import subprocess
from pipeline.tasks import task_base
from pipeline.tasks.requirements import format_requirements


class JavaFormatTask(task_base.TaskBase):

    def execute(self, output_dir):
        print 'Formatting files in ' + os.path.abspath(output_dir)
        # TODO(shinfan): figure out how to get this distributed and made
        # available to the pipeline instead of having to do a download.
        path = os.path.join(format_requirements.JavaFormatRequirement.DIR,
                            format_requirements.JavaFormatRequirement.FILENAME)
        for root, dirs, files in os.walk(output_dir):
            for filename in files:
                if filename.endswith('.java'):
                    output = os.path.abspath(os.path.join(root, filename))
                    # TODO: Store both intermediate and final output.
                    subprocess.call(
                        ['java', '-jar', path, '--replace', output])
        return

    def validate(self):
        return [format_requirements.JavaFormatRequirement]
