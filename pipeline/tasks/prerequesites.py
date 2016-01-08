"""Utilities related to prerequesite checks"""


class PrerequesiteError(Exception):
    def __init__(self, prerequesite, msg):
        self.prerequesite = prerequesite
        self.msg = msg
    def __str__(self):
        return 'Missing prerequesite: {0}. {1}'.format(
            self.prerequesite, self.msg)
