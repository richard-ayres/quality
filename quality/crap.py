'''
Calculate C.R.A.P. scores for Python modules.

For background on C.R.A.P., see http://www.artima.com/weblogs/viewpost.jsp?thread=215899
'''

import ast
import quality.dec

def gen_class_elems(doc):
    '''
    yield 'class' elements from a coverage.xml document
    '''
    for package_elem in doc.getroot()[0]:
        for class_elem in package_elem[0]:
            yield class_elem

def extract_line_nums(doc, source_path):
    '''
    Extract a two sets of line numbers from coverage.xml: "hit" and "missed" lines.
    
    `doc` - etree-style document representing coverage.xml
    `source_path` - the path to the file under test
    '''
    for class_elem in gen_class_elems(doc):
        if class_elem.get('filename') == source_path:
            break
    else:
        raise ValueError('couldn\'t find coverage data for source file "%s" in coverage.xml document' % source_path)

    hit_lines = set()
    missed_lines = set()
    for line_elem in class_elem[1]:
        (hit_lines if line_elem.get('hits') == '1' else missed_lines).add(int(line_elem.get('number')))

    return hit_lines, missed_lines

class CrapJudge(object):
    '''
    Calculates C.R.A.P. scores for Contestants.

    Implementation note: this is a bit wonky as a class.  It's done so to
    avoid having to re-parse the coverage.xml and re-calculate hit and 
    missed lines for each contestant.

    It might be better to give each judge a separate entry point for:
    (1) each source file
    (2) each Contestant
    (3) its own initialization / receiving instance options from command-line 
        opts?

    But this begs the question of how command-line options are handed to
    Judge instances; are there per-source, per-Contestant, and per-instance
    options?  Our only extant option, `coverage_file`, would be per-source.

    Attributes:

    * coverage - dict mapping filenames to sets of line numbers, (hit_lines, missed_lines)
    * unified - dict mapping filenames to sets of all line numbers in coverage.xml: hit_lines | missed_lines
    '''
    def __init__(self):
        self.coverage = {}
        self.unified = {}
        
    def coverage_ratio(self, contestant):
        '''
        Find the proportion of the line numbers for `contestant` that were 
        reported covered in coverage.xml.

        Returns a float.
        '''
        if len(contestant.linenums) == 0:
            # if a def has no lines, we'll call it 100% covered.
            return 1.0

        fixed_lines = self.align_linenums(contestant)
        
        return float(len(fixed_lines & self.coverage[contestant.src_file][0])) / len(fixed_lines)

    def align_linenums(self, contestant):
        '''
        Return a set of linenums in `contestant`, adjusted so they match the 
        line numbers reported by coverage.xml.

        We do this by filtering out lines that don't appear in the union of
        hit and missed lines from coverage.xml.  This assumes that every 
        line number in the contestant is also in coverage.xml.

        Background:
        coverage.xml is produced by coverage.py, which gets line numbers 
        of executed code from cPython.  This differs from the line numbers
        generated by the ast module, as described here:
        https://bitbucket.org/ned/coveragepy/issue/180/last-of-certain-multi-line-statements-is
        '''
        return contestant.linenums & self.unified[contestant.src_file]

    @quality.dec.judge('crap')
    def judge_crap(self, contestant, coverage_file=None):
        '''
        '''
        if contestant.src_path not in self.coverage:
            coverage_doc = xml.etree.ElementTree.parse(coverage_file)
            hit, miss = extract_line_nums(coverage_doc, src_file)
            self.coverage[src_file] = (hit, miss)
            self.unified[src_file] = hit | miss
    
        complexity = quality.complexity.complexity(contestant.node)
        cov_ratio = self.coverage_ratio(contestant, hit_lines)

        return (complexity ** 2) * (1 - cov_ratio) + complexity
