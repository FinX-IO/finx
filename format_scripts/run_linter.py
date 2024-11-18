#! python
"""
author: dick mule
purpose: lint code base
"""
import sys

from pylint.lint import Run


def main(local: bool = False):
    results = Run(['./finx/' if local else '/finx/'], exit=False)
    if results.linter.stats.global_note < 10.:
        raise Exception('Codebase is not fully linted!')


if __name__ == '__main__':
    main(sys.argv[-1] == 'LOCAL')
